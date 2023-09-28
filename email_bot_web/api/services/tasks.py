import asyncio
import base64
import quopri
import re
from asyncio import wait_for
from collections import namedtuple
from email.header import decode_header
from email.message import Message
from email.parser import BytesHeaderParser, BytesParser
from typing import Collection

import aioimaplib
import chardet  # type: ignore
from bs4 import BeautifulSoup
from email_service.schema import ImapEmailModel

IMAP_SERVERS = {
    'google': 'imap.gmail.com',
    'yandex': 'imap.yandex.com',
    'yahoo': 'imap.mail.yahoo.com',
    'outlook': 'outlook.office365.com',
    'mail': 'imap.mail.ru',
}

ID_HEADER_SET = {'Content-Type', 'From', 'To', 'Cc', 'Bcc', 'Date', 'Subject',
                 'Message-ID', 'In-Reply-To', 'References'}
FETCH_MESSAGE_DATA_UID = re.compile(rb'.*UID (?P<uid>\d+).*')
FETCH_MESSAGE_DATA_SEQNUM = re.compile(rb'(?P<seqnum>\d+) FETCH.*')
FETCH_MESSAGE_DATA_FLAGS = re.compile(rb'.*FLAGS \((?P<flags>.*?)\).*')
MessageAttributes = namedtuple('MessageAttributes', 'uid flags sequence_number')


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
                        body_parts.append(self.clean_email_body(decoded_body))

                    else:
                        body_parts.append(decoded_body)
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
    def __init__(self, host, user, password, whitelist=None, callback=None):
        self.host = host
        self.user = user
        self.password = password
        self.persistent_max_uid = 1
        self.whitelist = set(whitelist) if whitelist else None
        self._stop_flag = False
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
        self._stop_flag = True

    async def fetch_messages_headers(self, imap_client: aioimaplib.IMAP4_SSL, max_uid: int) -> int:
        try:
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
                            await self.callback(email_object)

                        await self.mark_as_read(imap_client, new_max_uid)
            else:
                print('error %s' % response)
            return new_max_uid

        except aioimaplib.aioimaplib.CommandTimeout as e:
            print(f'CommandTimeout error occurred: {e}')
            await asyncio.sleep(10)  # Подождать 10 секунд перед попыткой снова
            return await self.fetch_messages_headers(imap_client, max_uid)

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

    @staticmethod
    def handle_server_push(push_messages: Collection[bytes]) -> None:
        for msg in push_messages:
            if msg.endswith(b'EXISTS'):
                print('new message: %r' % msg)
            elif msg.endswith(b'EXPUNGE'):
                print('message removed: %r' % msg)
            elif b'FETCH' in msg and b'\\Seen' in msg:
                print('message seen %r' % msg)
            else:
                print('unprocessed push message : %r' % msg)

    async def imap_loop(self) -> None:
        imap_client = aioimaplib.IMAP4_SSL(host=self.host, timeout=60)
        await imap_client.wait_hello_from_server()

        await imap_client.login(self.user, self.password)
        await imap_client.select('INBOX')

        while not self._stop_flag:
            self.persistent_max_uid = await self.fetch_messages_headers(imap_client, self.persistent_max_uid)
            # logging.info('%s starting idle' % self.user)
            idle_task = await imap_client.idle_start(timeout=180)
            # self.handle_server_push(await imap_client.wait_server_push())
            imap_client.idle_done()
            await wait_for(idle_task, timeout=300)
            # logging.info('%s ending idle' % self.user)
        await imap_client.logout()

    @staticmethod
    async def mark_as_read(imap_client: aioimaplib.IMAP4_SSL, uid: int) -> None:
        await imap_client.uid('store', str(uid), '+FLAGS', '(\\Seen)')


class IMAPListener:
    def __init__(self, host, user, password, callback=None):
        self.imap_client = IMAPClient(host=host, user=user, password=password, callback=callback)
        self._task = None

    async def start(self):
        if self._task is None:
            self._task = asyncio.create_task(self.imap_client.imap_loop())

    async def stop(self):
        if self._task:
            self.imap_client.stop_listening()
            await self._task
            self._task = None


async def process_email(email_object):
    # Логика обработки письма из объекта письма, преобразования в фото и передача дальше
    print(f'Date: {email_object.date}')
    print(f'From: {email_object.from_}')
    print(f'To: {email_object.to}')
    print(f'Subject: {email_object.subject}')
    print(f'Body: {email_object.body}')
    pass
