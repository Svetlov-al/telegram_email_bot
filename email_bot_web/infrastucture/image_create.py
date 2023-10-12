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

    IMAGE_MIN_WIDTH = 300
    IMAGE_MIN_HEIGHT = 300
    IMAGE_PADDING = 20

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

            image = Image.open(temp_path)
            image = image.convert('RGBA')

            width, height = image.size
            for x in range(width):
                for y in range(height):
                    r, g, b, a = image.getpixel((x, y))
                    if r == 255 and g == 255 and b == 255:
                        image.putpixel((x, y), (r, g, b, 0))

            bbox = image.getbbox()
            x_min, y_min, x_max, y_max = bbox
            x_min -= self.IMAGE_PADDING
            y_min -= self.IMAGE_PADDING
            x_max += self.IMAGE_PADDING
            y_max += self.IMAGE_PADDING
            cropped_image = image.crop((x_min, y_min, x_max, y_max))

            cropped_width, cropped_height = cropped_image.size
            if cropped_width < self.IMAGE_MIN_WIDTH:
                left = (cropped_width - self.IMAGE_MIN_WIDTH) // 2
                right = left + self.IMAGE_MIN_WIDTH
                cropped_image = cropped_image.crop((left, 0, right, cropped_height))
            if cropped_height < self.IMAGE_MIN_HEIGHT:
                top = (cropped_height - self.IMAGE_MIN_HEIGHT) // 2
                bottom = top + self.IMAGE_MIN_HEIGHT
                cropped_image = cropped_image.crop((0, top, cropped_width, bottom))

            byte_stream = io.BytesIO()
            cropped_image.save(byte_stream, format='PNG')
            byte_stream.seek(0)

            os.remove(temp_path)

            return byte_stream
        except Exception as e:
            logger.error(f'Ошибка при создании изображения из письма: {e}')
            raise ValueError('Из данного письма невозможно сделать картинку')
