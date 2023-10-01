import asyncio
import json

from api.repositories.repositories import EmailBoxRepository
from api.services.tools import redis_client
from celery import shared_task

email_repo = EmailBoxRepository

global_loop = None


@shared_task
def sync_email_listening_status():
    global global_loop
    if global_loop is None or global_loop.is_closed():
        global_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(global_loop)
    global_loop.run_until_complete(email_listening_status())


async def email_listening_status():
    """Функция синхронизации статуса слушателя почты между базой и редисом"""

    all_email_boxes = await email_repo.get_all_boxes()

    for email_box in all_email_boxes:

        db_status = email_box.listening

        user_key = f'user:{email_box.email_username}'
        user_data_str = await redis_client.get_key(user_key)
        redis_status = json.loads(user_data_str).get('listening', None) if user_data_str else None

        if redis_status is not None and redis_status != db_status:
            user_data = json.loads(user_data_str)
            user_data['listening'] = db_status
            await redis_client.set_key(user_key, json.dumps(user_data))
    return
