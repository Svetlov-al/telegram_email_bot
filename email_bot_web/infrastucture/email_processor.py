import io
import os
import re
import uuid
from typing import Any

from api.services.box_filter_services import BoxFilterService
from email_service.schema import ImapEmailModel
from html2image import Html2Image
from infrastucture.logger_config import logger
from PIL import Image

filters = BoxFilterService

EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'


class EmailToImage:
    """Класс для преобразования из текста/html разметки в изображение с содержимым"""

    def __init__(self, width: int = 1920, height: int = 1080) -> None:
        self.width = width
        self.height = height
        self.hti = Html2Image(browser='chromium', keep_temp_files=False)
        self.hti.browser.flags = [
            '--no-sandbox',
            '--headless',
            '--disable-gpu',
            '--hide-scrollbars'
        ]

        self.hti.size = (self.width, self.height)

    @classmethod
    def generate_unique_filename(cls, extension: str = '.png') -> str:
        """Метод генерации уникального имени файла."""

        return f'{uuid.uuid4()}{extension}'

    def generate_image(self, text: str, save_path: str) -> None:
        """Метод преобразования текста в изображение с сохранением в контейнере."""

        self.hti.screenshot(html_str=text, save_as=save_path)

    def generate_image_to_send(self, text: str) -> io.BytesIO:
        """Метод преобразования текста в изображение для отправки в байтах."""

        temp_path = self.generate_unique_filename()
        self.hti.screenshot(html_str=text, save_as=temp_path)

        # Загрузка изображения и сохранение его в байтовый поток
        image = Image.open(temp_path)
        byte_stream = io.BytesIO()
        image.save(byte_stream, format='PNG')
        byte_stream.seek(0)

        os.remove(temp_path)

        return byte_stream


async def process_email(email_object: ImapEmailModel, telegram_id: int, email_username: str) -> None:
    """Обработка письма, сортировка по фильтрам, преобразование в фотографию"""

    list_of_filters: list[dict | Any] = await filters.get_filters_for_user_and_email(telegram_id, email_username)
    email_sender_matches = re.findall(EMAIL_PATTERN, email_object.from_)
    if email_sender_matches:
        email_sender = email_sender_matches[0]
        logger.info(f'OUR_SERNDER_TO_MATCH_WITH_FILTER - {email_sender}')
        for filter_ in list_of_filters:
            if isinstance(filter_, dict):
                value = filter_['filter_value']
            else:
                value = filter_.filter_value
            if value == email_sender:
                email_to_image = EmailToImage()
                logger.info(f'Date: {email_object.date}')
                logger.info(f'From: {email_object.from_}')
                logger.info(f'To: {email_object.to}')
                logger.info(f'Subject: {email_object.subject}')
                logger.info(f'Body: {email_object.body}')

    email_content = f"""
    Дата письма: {email_object.date}<br>
    От кого: {email_object.from_}<br>
    Кому: {email_object.to}<br>
    Тема: {email_object.subject}<br>
    Сообщение: {email_object.body}
    """
    email_to_image = EmailToImage()
    email_to_image.generate_image(email_content, EmailToImage.generate_unique_filename())
