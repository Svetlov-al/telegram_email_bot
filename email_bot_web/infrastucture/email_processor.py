import re
from typing import Any

from aioimaplib import aioimaplib
from api.services.box_filter_services import BoxFilterService
from email_service.schema import ImapEmailModel
from infrastucture.logger_config import logger
from infrastucture.tasks import handle_email_to_image

filters = BoxFilterService

EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'


async def mark_as_read(imap_client: aioimaplib.IMAP4_SSL, uid: int) -> None:
    """
    Отмечает указанное письмо как прочитанное на IMAP-сервере.

    Эта функция использует IMAP-команду 'store' для установки флага 'Seen'
    для письма с заданным UID. После выполнения этой функции, письмо будет
    отображаться как прочитанное на почтовом сервере и в любых почтовых клиентах,
    которые синхронизируются с этим сервером.

    Параметры:
    - imap_client (aioimaplib.IMAP4_SSL): Экземпляр IMAP-клиента для взаимодействия с IMAP-сервером.
    - uid (int): Уникальный идентификатор письма, которое необходимо отметить как прочитанное.

    Возвращает:
    None: Функция не возвращает значений, но может вызвать исключения в случае ошибок.
    """
    await imap_client.uid('store', str(uid), '+FLAGS', '(\\Seen)')


async def process_email(email_object: ImapEmailModel, telegram_id: int, email_username: str,
                        uid: int, imap_client: aioimaplib.IMAP4_SSL) -> None:
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
                logger.info(f'Date: {email_object.date}')
                logger.info(f'From: {email_object.from_}')
                logger.info(f'To: {email_object.to}')
                logger.info(f'Subject: {email_object.subject}')
                logger.info(f'Body: {email_object.body}')
                await mark_as_read(imap_client, uid)

                email_content = f"""
                    Дата письма: {email_object.date}<br>
                    От кого: {email_object.from_}<br>
                    Кому: {email_object.to}<br>
                    Тема: {email_object.subject}<br>
                    Сообщение: {email_object.body}
                    """
                handle_email_to_image.delay(email_content, telegram_id, email_sender)
