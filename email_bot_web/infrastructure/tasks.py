import json

from api.repositories.repositories import EmailBoxRepository
from celery import shared_task
from email_service.models import EmailBox
from infrastructure.bot_utils import TelegramBotSender
from infrastructure.image_create import EmailToImage
from infrastructure.logger_config import logger
from infrastructure.tools import CACHE_PREFIX, redis_client

email_repo = EmailBoxRepository


@shared_task
def sync_email_listening_status() -> None:
    """Функция синхронизации статуса слушателя почты между базой и редисом"""

    all_email_boxes: list[EmailBox] = email_repo.sync_get_all_boxes()

    for email_box in all_email_boxes:

        db_status: bool = email_box.listening

        user_key = f'user:{email_box.email_username}'
        user_data_str = redis_client.get_key(user_key)

        if user_data_str:
            redis_status = json.loads(user_data_str).get('listening', None)

            if redis_status is not None and redis_status != db_status:
                user_data = json.loads(user_data_str)
                user_data['listening'] = db_status
                redis_client.set_key(user_key, json.dumps(user_data))
                user_key_email_box = f'{CACHE_PREFIX}email_box_{email_box.user_id}_{email_box.email_username}'
                redis_client.delete_key(user_key_email_box)
    return


@shared_task
def handle_email_to_image(email_content: str,
                          telegram_id: int,
                          email_sender) -> None:
    try:
        email_to_image = EmailToImage()
        our_image_to_send = email_to_image.generate_image_to_send(email_content)
        notification_text = f'<b>Поступило новое письмо от:\n{email_sender}</b>\n'
        TelegramBotSender.send_image_sync(chat_id=telegram_id, image_stream=our_image_to_send,
                                          text=notification_text)
    except ValueError as e:
        logger.error(e)
