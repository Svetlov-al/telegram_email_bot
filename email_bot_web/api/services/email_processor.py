import re

from api.services.box_filter_services import BoxFilterService
from PIL import Image, ImageDraw, ImageFont

filters = BoxFilterService


EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'


class EmailToImage:
    def __init__(self, width=800, height=600, font_size=20):
        self.width = width
        self.height = height
        self.font_size = font_size

    def generate_image(self, text):
        # Создание нового изображения с белым фоном
        img = Image.new('RGB', (self.width, self.height), color='white')
        d = ImageDraw.Draw(img)

        # Загрузка шрифта
        font = ImageFont.load_default()

        # Разбивка текста на строки, чтобы он помещался в изображение
        y_text = 10
        line_height = 20  # фиксированная высота строки

        # Игнорирование символов, которые не поддерживаются шрифтом
        safe_text = text.encode('latin-1', errors='ignore').decode('latin-1')
        d.multiline_text((10, y_text), safe_text, font=font, fill='black', spacing=line_height)

        return img


async def process_email(email_object, telegram_id, email_username):
    """Обработка письма, сортировка по фильтрам, преобразование в фотографию"""

    list_of_filters = await filters.get_filters_for_user_and_email(telegram_id, email_username)
    email_sender_matches = re.findall(EMAIL_PATTERN, email_object.from_)
    if email_sender_matches:
        email_sender = email_sender_matches[0]
        print(f'OUR_SERNDER_TO_MATCH_WITH_FILTER - {email_sender}')
        for filter_ in list_of_filters:
            print(filter_.filter_value)
            if filter_.filter_value == email_sender:
                email_to_image = EmailToImage()
                print(f'Date: {email_object.date}')
                print(f'From: {email_object.from_}')
                print(f'To: {email_object.to}')
                print(f'Subject: {email_object.subject}')
                print(f'Body: {email_object.body}')
                email_content = f"""
                        Date: {email_object.date}
                        From: {email_object.from_}
                        To: {email_object.to}
                        Subject: {email_object.subject}
                        Body: {email_object.body}
                        """
                img = email_to_image.generate_image(email_content)
                img.save('output_image.png')
