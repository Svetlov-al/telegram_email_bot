import asyncio
import base64
import json
import quopri
import re
from asyncio import CancelledError, TimeoutError, wait_for
from collections import namedtuple
from email.header import decode_header
from email.message import Message
from email.parser import BytesHeaderParser, BytesParser
from typing import Collection

import aioimaplib
import chardet  # type: ignore
from api.repositories.repositories import (
    BoxFilterRepository,
    EmailBoxRepository,
    EmailServiceRepository,
)
from api.services.tools import redis_client
from bs4 import BeautifulSoup
from email_service.schema import ImapEmailModel

ID_HEADER_SET = {'Content-Type', 'From', 'To', 'Cc', 'Bcc', 'Date', 'Subject',
                 'Message-ID', 'In-Reply-To', 'References'}
FETCH_MESSAGE_DATA_UID = re.compile(rb'.*UID (?P<uid>\d+).*')
FETCH_MESSAGE_DATA_SEQNUM = re.compile(rb'(?P<seqnum>\d+) FETCH.*')
FETCH_MESSAGE_DATA_FLAGS = re.compile(rb'.*FLAGS \((?P<flags>.*?)\).*')
MessageAttributes = namedtuple('MessageAttributes', 'uid flags sequence_number')

email_service_repo = EmailServiceRepository
email_repo = EmailBoxRepository
box_filter_repo = BoxFilterRepository


MAX_RETRIES = 5


class EmailDecoder:
    @staticmethod
    def decode_header_content(header_content) -> str:
        decoded_content = decode_header(header_content)
        return ''.join(
            [text.decode(charset or 'utf-8') if isinstance(text, bytes) else text for text, charset in decoded_content])

    @staticmethod
    def decode_payload(payload, content_transfer_encoding, encoding):
        if isinstance(payload, str):
            return payload

        if content_transfer_encoding == 'base64':
            # Если payload является строкой, преобразуем ее в байты
            if isinstance(payload, str):
                payload = payload.encode(encoding)

            # Добавляем padding, если он отсутствует
            padding_needed = len(payload) % 4
            if padding_needed:
                payload += b'=' * (4 - padding_needed)
            return base64.b64decode(payload).decode(encoding, errors='replace')

        elif content_transfer_encoding == 'quoted-printable':
            return quopri.decodestring(payload).decode(encoding, errors='replace')

        elif content_transfer_encoding == '7bit' or content_transfer_encoding == '8bit':
            return payload.decode(encoding, errors='replace')

        else:
            detected_encoding = chardet.detect(payload)['encoding']
            return payload.decode(detected_encoding, errors='replace')

    def get_email_body(self, email_obj: Message) -> str:
        body_parts = []

        if email_obj.is_multipart():
            html_body = None
            text_body = None
            for part in email_obj.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition'))
                content_transfer_encoding = part.get('Content-Transfer-Encoding')
                payload = part.get_payload(decode=True)

                if payload is None:
                    continue

                encoding = part.get_content_charset() or chardet.detect(payload)['encoding']

                if 'attachment' not in content_disposition:
                    decoded_body = self.decode_payload(payload, content_transfer_encoding, encoding)

                    if content_type == 'text/html':
                        html_body = self.clean_email_body(decoded_body)
                    else:
                        text_body = decoded_body

            body_parts.append(str(html_body if html_body else text_body))
        else:
            content_transfer_encoding = email_obj.get('Content-Transfer-Encoding')
            payload = email_obj.get_payload()
            encoding = email_obj.get_content_charset() or chardet.detect(payload.encode('utf-8'))['encoding']
            decoded_payload = self.decode_payload(payload, content_transfer_encoding, encoding)
            body_parts.append(self.clean_email_body(decoded_payload))

        full_body = '\n\n'.join(body_parts)
        return full_body[:500]

    def get_email_subject(self, email_obj) -> str:
        return self.decode_header_content(email_obj['subject'])

    def get_email_sender(self, email_obj) -> str:
        return self.decode_header_content(email_obj['from'])

    def get_email_recipient(self, email_obj) -> str:
        return self.decode_header_content(email_obj['to'])

    def get_email_date(self, email_obj) -> str:
        return self.decode_header_content(email_obj['Date'])

    @staticmethod
    def clean_email_body(body_part) -> str:
        soup = BeautifulSoup(body_part, 'html.parser')

        # Удаляем все теги (ссылки)
        for a in soup.find_all('a'):
            a.decompose()

        # Удаляем все теги <img> (изображения) и заменяем их на текст "картинка"
        for img in soup.find_all('img'):
            img.replace_with('картинка')

        return soup.get_text().strip()

    @staticmethod
    def clean_excessive_newlines(text: str) -> str:
        return ' '.join(text.split())

    def get_cleaned_email_details(self, email_obj) -> dict:
        body = self.get_email_body(email_obj)
        body = self.clean_excessive_newlines(body)
        subject = self.get_email_subject(email_obj)
        sender = self.get_email_sender(email_obj)
        recipient = self.get_email_recipient(email_obj)
        date = self.get_email_date(email_obj)

        return {
            'body': body,
            'subject': subject,
            'sender': sender,
            'recipient': recipient,
            'date': date
        }


class IMAPClient(EmailDecoder):
    def __init__(self, host, user, password, telegram_id, whitelist=None, callback=None):
        self.host = host
        self.user = user
        self.telegram_id = telegram_id
        self.password = password
        self.persistent_max_uid = 1
        self.whitelist = set(whitelist) if whitelist else None
        self.should_stop = False
        self.callback = callback

    @staticmethod
    def extract_email(encoded_str):
        decoded_list = decode_header(encoded_str)

        decoded_string = ''.join(
            [t[0].decode(t[1] or 'ascii') if isinstance(t[0], bytes) else t[0] for t in decoded_list])

        email_pattern = r'[\w\.-]+@[\w\.-]+'
        match = re.search(email_pattern, decoded_string)
        email_address = match.group(0) if match else None

        return email_address

    def stop_listening(self):
        self.should_stop = True

    async def fetch_messages_headers(self, imap_client: aioimaplib.IMAP4_SSL, max_uid: int) -> int:
        response = await imap_client.uid('fetch', '%d:*' % (max_uid + 1),
                                         '(UID FLAGS BODY.PEEK[HEADER.FIELDS (%s)])' % ' '.join(ID_HEADER_SET))
        new_max_uid = max_uid
        last_message_headers = None
        if response.result == 'OK':
            for i in range(0, len(response.lines) - 1, 3):
                fetch_command_without_literal = b'%s %s' % (response.lines[i], response.lines[i + 2])

                match_result = FETCH_MESSAGE_DATA_UID.match(fetch_command_without_literal)
                uid = 0
                if match_result:
                    uid = int(match_result.group('uid'))

                if uid > max_uid:
                    last_message_headers = BytesHeaderParser().parsebytes(response.lines[i + 1])
                    new_max_uid = uid
            if last_message_headers:
                if not self.whitelist or \
                        (self.whitelist and self.extract_email(last_message_headers.get('From')) in self.whitelist):
                    email_details = await self.fetch_message_details(imap_client, new_max_uid)
                    formatted_email_dict = self.format_email(email_details)
                    email_object = ImapEmailModel(**formatted_email_dict)

                    if self.callback:
                        await process_email(email_object, telegram_id=self.telegram_id, email_username=self.user)
        else:
            print('error %s' % response)
        return new_max_uid

    @staticmethod
    async def fetch_message_body(imap_client: aioimaplib.IMAP4_SSL, uid: int) -> Message:
        dwnld_resp = await imap_client.uid('fetch', str(uid), 'BODY.PEEK[]')
        return BytesParser().parsebytes(dwnld_resp.lines[1])

    async def fetch_message_details(self, imap_client: aioimaplib.IMAP4_SSL, uid: int) -> dict:
        dwnld_resp = await imap_client.uid('fetch', str(uid), 'BODY.PEEK[]')
        message = BytesParser().parsebytes(dwnld_resp.lines[1])
        email_details = self.get_cleaned_email_details(message)
        return email_details

    @staticmethod
    def format_email(email_details: dict) -> dict:
        formatted_email = {
            'subject': email_details['subject'],
            'from_': email_details['sender'],
            'to': email_details['recipient'],
            'date': email_details['date'],
            'body': email_details['body']
        }
        return formatted_email

    async def handle_server_push(self, imap_client: aioimaplib.IMAP4_SSL, push_messages: Collection[bytes]) -> bool:
        for msg in push_messages:
            if msg.endswith(b'EXISTS'):
                imap_client.idle_done()
                print('new message: %r' % msg)
                self.persistent_max_uid = await self.fetch_messages_headers(imap_client, self.persistent_max_uid)
                await self.mark_as_read(imap_client, self.persistent_max_uid)
                return True
        return False
        # elif msg.endswith(b'EXPUNGE'):
        #     print('message removed: %r' % msg)
        # elif b'FETCH' in msg and b'\\Seen' in msg:
        #     print('message seen %r' % msg)
        # else:
        #     print('unprocessed push message : %r' % msg)

    async def imap_loop(self) -> None:
        print(f'{self.user} - Подключение к серверу...')
        imap_client = aioimaplib.IMAP4_SSL(host=self.host, timeout=60)
        await imap_client.wait_hello_from_server()
        print(f'{self.user} - Авторизация...')
        await imap_client.login(self.user, self.password)
        print(f'{self.user} - Выбор папки INBOX...')
        await imap_client.select('INBOX')

        while not self.should_stop:
            user_key = f'user:{self.user}'
            user_data_str = await redis_client.get_key(user_key)
            if user_data_str:
                user_data = json.loads(user_data_str)
                if not user_data['listening']:
                    self.should_stop = True
            print('%s starting idle' % self.user)
            try:
                idle_task = await imap_client.idle_start(timeout=59)
                push = await self.handle_server_push(imap_client, await imap_client.wait_server_push())
                if not push:
                    imap_client.idle_done()

                await wait_for(idle_task, timeout=300)

            except (TimeoutError, CancelledError):
                print(f'Превышено время ожидания на почте {self.user}! Перезапускаем режим idle...')
                await asyncio.sleep(10)
                imap_client.idle_done()
                retries = 0

                while retries < MAX_RETRIES:
                    try:
                        await imap_client.logout()
                        print(f'{self.user} - Подключение к серверу...')
                        imap_client = aioimaplib.IMAP4_SSL(host=self.host, timeout=60)
                        await imap_client.wait_hello_from_server()
                        print(f'{self.user} - Авторизация...')
                        await imap_client.login(self.user, self.password)
                        print(f'{self.user} - Выбор папки INBOX...')
                        await imap_client.select('INBOX')
                        await imap_client.idle_start(timeout=59)
                        break  # если соединение установлено успешно, выходим из цикла
                    except Exception as e:
                        print(f'Ошибка при попытке переподключения для {self.user}: {e}')
                        retries += 1
                        await asyncio.sleep(10)  # задержка перед следующей попыткой
                if retries == MAX_RETRIES:
                    print(f'Не удалось переподключиться к {self.user} после {MAX_RETRIES} попыток.')
        await imap_client.logout()

    @staticmethod
    async def mark_as_read(imap_client: aioimaplib.IMAP4_SSL, uid: int) -> None:
        await imap_client.uid('store', str(uid), '+FLAGS', '(\\Seen)')


class IMAPListener:
    def __init__(self, host, user, password, telegram_id, callback=None):
        self.imap_client = IMAPClient(host=host, user=user, telegram_id=telegram_id, password=password,
                                      callback=callback)
        self._task = None
        self.user = user

    async def start(self):
        if self._task is None:
            self._task = asyncio.create_task(self.imap_client.imap_loop())

    async def stop(self):
        if self._task:
            self.imap_client.stop_listening()
            await self._task
            self._task = None
            print(f'Task for {self.user} was stopped!')


async def start_listening_all_emails():
    all_emails = await email_repo.get_all_boxes()

    for email_data in all_emails:
        email_service = await email_service_repo.get_host_by_slug(email_data.email_service.slug)
        if not email_service:
            print(f'Email service with slug {email_data.email_service.slug} does not exist')
            continue
        host = email_service.address

        listener = IMAPListener(
            host=host,
            user=email_data.email_username,
            password=email_data.email_password,
            telegram_id=email_data.user_id,
            callback=process_email
        )
        await listener.start()

        user_key = f'user:{email_data.email_username}'
        user_data = {
            'telegram_id': email_data.user_id.telegram_id,
            'email_username': email_data.email_username,
            'listening': True
        }

        try:
            await redis_client.set_key(user_key, json.dumps(user_data))
        except Exception as e:
            print(e)


async def process_email(email_object, telegram_id, email_username):
    # Логика обработки письма из объекта письма, преобразования в фото и передача дальше
    print(telegram_id)
    print(email_username)
    print(f'Date: {email_object.date}')
    print(f'From: {email_object.from_}')
    print(f'To: {email_object.to}')
    print(f'Subject: {email_object.subject}')
    print(f'Body: {email_object.body}')
    pass
