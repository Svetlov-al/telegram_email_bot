import re
from typing import Any

from api.services.box_filter_services import BoxFilterService
from infrastucture.logger_config import logger
from PIL import Image, ImageDraw, ImageFont

filters = BoxFilterService


EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'


class EmailToImage:
    """Создает из текста изображение с содержимым"""

    def __init__(self, width: int = 800, height: int = 600, font_size: int = 20) -> None:
        self.width = width
        self.height = height
        self.font_size = font_size

    def generate_image(self, text: str) -> Image.Image:

        img = Image.new('RGB', (self.width, self.height), color='white')
        d = ImageDraw.Draw(img)

        font = ImageFont.load_default()

        # Разбивка текста на строки, чтобы он помещался в изображение
        y_text = 10
        line_height = 20

        # Игнорирование символов, которые не поддерживаются шрифтом
        safe_text = text.encode('latin-1', errors='ignore').decode('latin-1')
        d.multiline_text((10, y_text), safe_text, font=font, fill='black', spacing=line_height)

        return img


async def process_email(email_object: Any, telegram_id: int, email_username: str) -> None:
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
                        Date: {email_object.date}
                        From: {email_object.from_}
                        To: {email_object.to}
                        Subject: {email_object.subject}
                        Body: {email_object.body}
                        """
                img = email_to_image.generate_image(email_content)
                img.save('output_image.png')
