import asyncio
import json
import os
import re
from asyncio import CancelledError, TimeoutError, wait_for
from collections import namedtuple
from email.header import decode_header
from email.message import Message
from email.parser import BytesHeaderParser, BytesParser
from typing import Callable, Collection

import aioimaplib
from api.repositories.repositories import EmailBoxRepository, EmailServiceRepository
from bs4 import BeautifulSoup
from crypto.crypto_utils import PasswordCipher
from email_service.models import EmailBox
from email_service.schema import ImapEmailModel
from infrastucture.email_processor import process_email
from infrastucture.exceptions import EmailCredentialsError
from infrastucture.logger_config import logger
from infrastucture.tools import redis_client

ID_HEADER_SET = {'Content-Type', 'From', 'To', 'Cc', 'Bcc', 'Date', 'Subject',
                 'Message-ID', 'In-Reply-To', 'References'}
FETCH_MESSAGE_DATA_UID = re.compile(rb'.*UID (?P<uid>\d+).*')
FETCH_MESSAGE_DATA_SEQNUM = re.compile(rb'(?P<seqnum>\d+) FETCH.*')
FETCH_MESSAGE_DATA_FLAGS = re.compile(rb'.*FLAGS \((?P<flags>.*?)\).*')
MessageAttributes = namedtuple('MessageAttributes', 'uid flags sequence_number')

email_domain_repo = EmailServiceRepository
email_repo = EmailBoxRepository

MAX_RETRIES = 5
RETRY_DELAY = 5


class EmailDecoder:
    @staticmethod
    def decode_header_content(header_content: str) -> str:
        decoded_content = decode_header(header_content)
        return ''.join(
            [text.decode(charset or 'utf-8') if isinstance(text, bytes) else text for text, charset in decoded_content])

    @staticmethod
    def get_email_body(email_obj: Message) -> str:
        """Извлекает тело письма из объекта письма."""

        plain_body = None
        html_body = None

        if email_obj.is_multipart():
            for part in email_obj.walk():
                content_type = part.get_content_type()
                charset = part.get_content_charset() or 'utf-8'
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        decoded_payload = payload.decode(charset, errors='replace')
                        if content_type == 'text/plain' and not plain_body:
                            plain_body = decoded_payload
                        elif content_type == 'text/html' and not html_body:
                            html_body = decoded_payload
                except Exception as e:
                    logger.error(e)
                    continue
        else:
            charset = email_obj.get_content_charset() or 'utf-8'
            try:
                payload = email_obj.get_payload(decode=True)
                if payload:
                    plain_body = payload.decode(charset, errors='replace')
            except Exception as e:
                logger.error(e)
                pass

        if html_body:
            return html_body
        elif plain_body:
            return plain_body
        else:
            return ''

    def get_email_subject(self, email_obj: Message) -> str:
        return self.decode_header_content(email_obj['subject'])

    def get_email_sender(self, email_obj: Message) -> str:
        return self.decode_header_content(email_obj['from'])

    def get_email_recipient(self, email_obj: Message) -> str:
        return self.decode_header_content(email_obj['to'])

    def get_email_date(self, email_obj: Message) -> str:
        return self.decode_header_content(email_obj['Date'])

    @staticmethod
    def clean_email_body(body_part: str) -> str:
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

    def get_cleaned_email_details(self, email_obj: Message) -> dict[str, str]:
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
    def __init__(self, host: str, user: str, password: str, telegram_id: int, callback: Callable | None = None):
        self.host = host
        self.user = user
        self.telegram_id = telegram_id
        self.password = password
        self.persistent_max_uid = 1
        self.should_stop = False
        self.callback = callback

    @staticmethod
    def extract_email(encoded_str: str) -> str | None:
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
        for attempt in range(MAX_RETRIES):
            try:
                response = await imap_client.uid('fetch', '%d:*' % max_uid,
                                                 '(UID FLAGS BODY.PEEK[HEADER.FIELDS (%s)])' % ' '.join(ID_HEADER_SET))
                new_max_uid = max_uid
                last_message_headers = None
                if response.result == 'OK':
                    uids_in_response = []
                    for i in range(0, len(response.lines) - 1, 3):
                        fetch_command_without_literal = b'%s %s' % (response.lines[i], response.lines[i + 2])
                        match_result = FETCH_MESSAGE_DATA_UID.match(fetch_command_without_literal)
                        uid = 0
                        if match_result:
                            uid = int(match_result.group('uid'))
                            uids_in_response.append(uid)

                        if uid > max_uid:
                            last_message_headers = BytesHeaderParser().parsebytes(response.lines[i + 1])
                            new_max_uid = uid

                    if max_uid not in uids_in_response:
                        new_max_uid = max(uids_in_response)

                    if last_message_headers:
                        email_details = await self.fetch_message_details(imap_client, new_max_uid)
                        formatted_email_dict = self.format_email(email_details)
                        email_object = ImapEmailModel(**formatted_email_dict)

                        if self.callback:
                            await process_email(email_object,
                                                telegram_id=self.telegram_id,
                                                email_username=self.user,
                                                imap_client=imap_client,
                                                uid=new_max_uid)
                    else:
                        logger.error(f'error {response}')
                    return new_max_uid

            except aioimaplib.aioimaplib.CommandTimeout:
                logger.error(
                    f'CommandTimeout error when fetching messages for UID {max_uid}. Attempt {attempt + 1} of {MAX_RETRIES}.')
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    logger.error(f'Failed to fetch messages for UID {max_uid} after {MAX_RETRIES} attempts.')
                    return max_uid
        return max_uid

    @staticmethod
    async def fetch_message(imap_client: aioimaplib.IMAP4_SSL, uid: int) -> Message:
        dwnld_resp = await imap_client.uid('fetch', str(uid), 'BODY.PEEK[]')
        return BytesParser().parsebytes(dwnld_resp.lines[1])

    async def fetch_message_details(self, imap_client: aioimaplib.IMAP4_SSL, uid: int) -> dict[str, str]:
        message = await self.fetch_message(imap_client, uid)
        email_details = self.get_cleaned_email_details(message)
        return email_details

    @staticmethod
    def format_email(email_details: dict) -> dict[str, str]:
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
                logger.info(f'new message: {msg!r}')
                last_uid = await self.fetch_messages_headers(imap_client, self.persistent_max_uid)
                if last_uid > self.persistent_max_uid:
                    self.persistent_max_uid = last_uid
                return True
        return False

    async def imap_loop(self):
        logger.info(f'{self.user} - Подключение к серверу...')
        imap_client = aioimaplib.IMAP4_SSL(host=self.host, timeout=60)
        await imap_client.wait_hello_from_server()
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f'{self.user} - Авторизация... Попытка {attempt + 1}')
                await imap_client.login(self.user, self.password)
                logger.info(f'{self.user} - Выбор папки INBOX...')
                await imap_client.select('INBOX')
                break
            except asyncio.exceptions.TimeoutError:
                logger.error(
                    f'Ошибка авторизации из-за превышения времени ожидания. Попытка {attempt + 1} из {MAX_RETRIES}')
                if attempt == MAX_RETRIES - 1:
                    logger.error(f'Не удалось авторизоваться после {MAX_RETRIES} попыток. Завершение работы.')
            except aioimaplib.aioimaplib.Abort:
                raise EmailCredentialsError(
                    f'Не удалось авторизоваться для {self.user} после {MAX_RETRIES} попыток.')
            await asyncio.sleep(RETRY_DELAY)

        # Проверка последнего письма перед началом прослушивания
        last_uid = await self.fetch_messages_headers(imap_client, self.persistent_max_uid)
        if last_uid > self.persistent_max_uid:
            # Если UID последнего письма больше сохраненного UID и письмо не прочитано, обрабатываем его
            self.persistent_max_uid = last_uid

        while not self.should_stop:
            user_key = f'user:{self.user}'
            user_data_str = redis_client.get_key(user_key)
            if user_data_str:
                user_data = json.loads(user_data_str)
                if not user_data['listening']:
                    self.should_stop = True
                    break
            else:
                self.should_stop = True
                break
            logger.info(f'{self.user} starting idle')
            try:
                idle_task = await imap_client.idle_start(timeout=59)
                push = await self.handle_server_push(imap_client, await imap_client.wait_server_push())
                if not push:
                    imap_client.idle_done()

                await wait_for(idle_task, timeout=300)
                logger.info(f'{self.user} ending idle')

            except (TimeoutError, CancelledError):
                logger.error(f'Превышено время ожидания на почте {self.user}! Перезапускаем режим idle...')
                await asyncio.sleep(10)
                imap_client.idle_done()
                retries = 0

                while retries < MAX_RETRIES:
                    try:
                        await imap_client.logout()
                        logger.info(f'{self.user} - Подключение к серверу...')
                        imap_client = aioimaplib.IMAP4_SSL(host=self.host, timeout=60)
                        await imap_client.wait_hello_from_server()
                        logger.info(f'{self.user} - Авторизация...')
                        await imap_client.login(self.user, self.password)
                        logger.info(f'{self.user} - Выбор папки INBOX...')
                        await imap_client.select('INBOX')
                        await imap_client.idle_start(timeout=59)
                        break
                    except Exception as e:
                        logger.error(f'Ошибка при попытке переподключения для {self.user}: {e}')
                        retries += 1
                        await asyncio.sleep(10)
                if retries == MAX_RETRIES:
                    logger.error(f'Не удалось переподключиться к {self.user} после {MAX_RETRIES} попыток.')

                    user_data_str = redis_client.get_key(user_key)
                    user_data = json.loads(user_data_str) if user_data_str else {}
                    email_box = await email_repo.get_by_email_username_for_user(self.telegram_id, self.user)
                    email_box_id = email_box.id
                    if email_box:
                        await email_repo.set_listening_status(email_box_id, False)
                    else:
                        logger.error(f'Почтовый ящик для {self.user} не найден!')
                    user_data['listening'] = False
                    redis_client.set_key(user_key, json.dumps(user_data))
                    redis_client.delete_key(f'email_boxes_for_user_{self.user}')
                    logger.info(f'Установлено значение listening в False для {self.user} в Redis.')
                    self.should_stop = True
        await imap_client.logout()


class IMAPListener:
    def __init__(self, host: str, user: str, password: str, telegram_id: int, callback: Callable | None = None):
        self.imap_client = IMAPClient(host=host, user=user, telegram_id=telegram_id, password=password,
                                      callback=callback)
        self._task = None
        self.user = user
        self.password = password
        self.host = host

    async def start(self):
        """Метод создания задачи на прослушивание почты."""

        if self._task is None:
            self._task = asyncio.create_task(self.imap_client.imap_loop())
            logger.info(f'Task for {self.user} was started!')

    async def stop(self):
        """Метод остановки задачи на прослушивание почты."""

        if self._task:
            self.imap_client.stop_listening()
            await self._task
            self._task = None
            logger.info(f'Task for {self.user} was stopped!')

    async def test_connection(self) -> bool:
        """
        Проверяет соединение и авторизацию на IMAP сервере.
        Возвращает True, если соединение и авторизация успешны.
        Генерирует исключение в случае ошибки.
        """
        try:
            imap_client = aioimaplib.IMAP4_SSL(host=self.host, timeout=10)
            await imap_client.wait_hello_from_server()
            login_response = await imap_client.login(self.user, self.password)
            if login_response.result != 'OK':
                return False
            else:
                return True
        except TimeoutError:
            raise TimeoutError('Connection to IMAP server timed out.')

    @classmethod
    async def create_and_start(cls, host: str, user: str, password: str, telegram_id: int,
                               callback: Callable | None = None) -> 'IMAPListener':
        """Метод класса для проверки валидности предоставленных данных и запуска прослушивания в случае успеха."""

        listener = cls(
            host=host,
            user=user,
            password=password,
            telegram_id=telegram_id,
            callback=callback
        )

        # Проверяем валидность предоставленных данных
        credentials = await listener.test_connection()
        if not credentials:
            raise EmailCredentialsError('Error with authorisation, check email or password!')

        await listener.start()

        return listener


async def start_listening_all_emails() -> None:
    """Функция запуска на прослушивание всех почтовых ящиков"""

    all_emails: list[EmailBox] = await email_repo.get_all_boxes()

    for email_data in all_emails:
        email_domain = await email_domain_repo.get_host_by_slug(email_data.email_service.slug)
        if not email_domain:
            logger.error(f'Email service with slug {email_data.email_service.slug} does not exist')
            continue

        if email_data.listening:
            host = email_domain.address

            cipher = PasswordCipher(key=os.getenv('ENCRYPTION_KEY'))
            decrypted_password = cipher.decrypt_password(email_data.email_password.encode())

            listener = IMAPListener(
                host=host,
                user=email_data.email_username,
                password=decrypted_password,
                telegram_id=email_data.user_id.telegram_id,
                callback=process_email
            )
            await listener.start()
        else:
            logger.info(f'Listening is set to False for email {email_data.email_username}. Skipping...')

        user_key = f'user:{email_data.email_username}'
        user_data = {
            'telegram_id': email_data.user_id.telegram_id,
            'email_username': email_data.email_username,
            'listening': email_data.listening
        }

        try:
            redis_client.set_key(user_key, json.dumps(user_data))
        except Exception as e:
            logger.error(e)
