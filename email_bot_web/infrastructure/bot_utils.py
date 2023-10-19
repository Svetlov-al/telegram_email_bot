import io
import json

import httpx
import requests
from django.conf import settings


class TelegramBotSender:
    """Класс для асинхронной отправки изображений и текста в Telegram бота."""

    @classmethod
    async def send_image(cls, chat_id: int, image_stream: io.BytesIO, text: str) -> None:
        """Асинхронный метод отправки изображения в Telegram бота."""
        url = settings.TELEGRAM_SEND_PHOTO_URL

        image_stream.seek(0)
        files = {'photo': ('image.png', image_stream, 'image/png')}
        keyboard = create_inline_keyboard()
        data = {
            'chat_id': chat_id,
            'caption': text,
            'parse_mode': 'HTML',
            'reply_markup': json.dumps(keyboard)
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, files=files)
            response.raise_for_status()

    @classmethod
    async def send_text(cls, chat_id: int, message: str) -> None:
        """Асинхронный метод отправки текста в Telegram бота."""
        url = settings.TELEGRAM_SEND_MESSAGE_URL

        data = {
            'chat_id': chat_id,
            'text': message
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            response.raise_for_status()

    @classmethod
    def send_image_sync(cls, chat_id: int, image_stream: io.BytesIO, text: str) -> None:
        """Синхронный метод отправки изображения в Telegram бота."""
        url = settings.TELEGRAM_SEND_PHOTO_URL

        image_stream.seek(0)
        files = {'photo': ('image.png', image_stream, 'image/png')}
        keyboard = create_inline_keyboard()
        data = {
            'chat_id': chat_id,
            'caption': text,
            'parse_mode': 'HTML',
            'reply_markup': json.dumps(keyboard)
        }

        response = requests.post(url, data=data, files=files)
        response.raise_for_status()


def create_inline_keyboard() -> dict[str, list[list[dict[str, str]]]]:
    """Создает инлайн клавиатуру для Telegram."""
    return {
        'inline_keyboard': [
            [
                {
                    'text': 'Скрыть уведомление',
                    'callback_data': 'hide_notification_message'
                }
            ]
        ]
    }
