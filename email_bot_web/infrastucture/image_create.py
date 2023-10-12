import io
import os
import uuid

from html2image import Html2Image
from infrastucture.logger_config import logger
from PIL import Image


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
            '--hide-scrollbars',
            '--disable-vulkan'
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
        try:
            temp_path = self.generate_unique_filename()
            self.hti.screenshot(html_str=text, save_as=temp_path)

            # Загрузка изображения и сохранение его в байтовый поток
            image = Image.open(temp_path)
            byte_stream = io.BytesIO()
            image.save(byte_stream, format='PNG')
            byte_stream.seek(0)

            os.remove(temp_path)

            return byte_stream
        except Exception as e:
            logger.error(f'Ошибка при создании изображения из письма: {e}')
            raise ValueError('Из данного письма невозможно сделать картинку')
