import io

import httpx
from django.conf import settings


class TelegramBotSender:
    """Класс для асинхронной отправки изображений и текста в Telegram бота."""

    @classmethod
    async def send_image(cls, chat_id: int, image_stream: io.BytesIO) -> None:
        """Асинхронный метод отправки изображения в Telegram бота."""
        url = settings.TELEGRAM_SEND_PHOTO_URL

        image_stream.seek(0)
        files = {'photo': ('image.png', image_stream, 'image/png')}
        data = {'chat_id': chat_id}

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
