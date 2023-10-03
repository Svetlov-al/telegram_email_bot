import json

from api.repositories.repositories import EmailBoxRepository
from api.services.tools import sync_redis_client
from celery import shared_task
from email_service.models import EmailBox

email_repo = EmailBoxRepository


@shared_task
def sync_email_listening_status() -> None:
    """Функция синхронизации статуса слушателя почты между базой и редисом"""

    all_email_boxes: list[EmailBox] = email_repo.sync_get_all_boxes()

    for email_box in all_email_boxes:

        db_status: bool = email_box.listening

        user_key = f'user:{email_box.email_username}'
        user_data_str = sync_redis_client.sync_get_key(user_key)

        if user_data_str:
            redis_status = json.loads(user_data_str).get('listening', None)

            if redis_status is not None and redis_status != db_status:
                user_data = json.loads(user_data_str)
                user_data['listening'] = db_status
                sync_redis_client.sync_set_key(user_key, json.dumps(user_data))
    return
