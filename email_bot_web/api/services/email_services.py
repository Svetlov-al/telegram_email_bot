import json

from api.repositories.repositories import (
    BoxFilterRepository,
    EmailBoxRepository,
    EmailServiceRepository,
)
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from email_service.models import EmailBox
from email_service.schema import (
    EmailBoxCreateSchema,
    EmailBoxOutputSchema,
    EmailServiceSchema,
)
from infrastucture.email_processor import process_email
from infrastucture.exceptions import (
    EmailAlreadyListeningError,
    EmailBoxByUsernameNotFoundError,
    EmailBoxCreationError,
    EmailBoxesNotFoundError,
    EmailBoxWithFiltersAlreadyExist,
    EmailBoxWithFiltersCreationError,
    EmailListeningError,
    EmailServiceSlugDoesNotExist,
    EmailServicesNotFoundError,
    UserDataNotFoundError,
)
from infrastucture.imap_listener import IMAPListener
from infrastucture.logger_config import logger
from infrastucture.tools import CACHE_PREFIX, cache_async, redis_client

email_repo = EmailBoxRepository
box_filter_repo = BoxFilterRepository
email_domain_repo = EmailServiceRepository


class EmailBoxService:

    @staticmethod
    async def create_email_box(data: EmailBoxCreateSchema) -> EmailBox:
        """Создает почтовый ящик для пользователя без фильтров и запуска прослушки почты"""

        try:
            email_box = await email_repo.create(data.user_id, data.email_service_slug, data.email_username,
                                                data.email_password)

            redis_client.delete_key(f'{CACHE_PREFIX}email_boxes_for_user_{data.user_id}')

            return email_box
        except (ObjectDoesNotExist, ValidationError) as e:
            raise EmailBoxCreationError(f'Error creating email box: {str(e)}')

    @staticmethod
    async def create_email_box_with_filters(data: EmailBoxCreateSchema) -> EmailBox:
        """Создает почтовый ящик с фильтрами для пользователя, запускает прослушку почты"""

        try:
            email_box = await email_repo.get_by_email_username_for_user(data.user_id, data.email_username)
            if email_box:
                raise EmailBoxWithFiltersAlreadyExist(
                    f'Email box with username {data.email_username} already exists for user {data.user_id}')

            email_box = await email_repo.create(data.user_id, data.email_service_slug,
                                                data.email_username, data.email_password)

            email_domain = await email_domain_repo.get_host_by_slug(data.email_service_slug)
            if not email_domain:
                raise EmailServiceSlugDoesNotExist(f'Email service with slug {data.email_service_slug} does not exist')

            await IMAPListener.create_and_start(host=email_domain.address,
                                                user=data.email_username,
                                                password=data.email_password,
                                                telegram_id=email_box.user_id.telegram_id,
                                                callback=process_email)

            user_key = f'user:{data.email_username}'

            user_data = {
                'telegram_id': data.user_id,
                'email_username': data.email_username,
                'listening': True
            }
            redis_client.set_key(user_key, json.dumps(user_data))

            for filter_data in data.filters:
                await box_filter_repo.create(email_box, filter_data.filter_value, filter_data.filter_name)

            redis_client.delete_key(f'{CACHE_PREFIX}email_boxes_for_user_{data.user_id}')

            return email_box
        except (ObjectDoesNotExist, ValidationError) as e:
            raise EmailBoxWithFiltersCreationError(f'Error creating email box with filters: {e}')

    @staticmethod
    @cache_async(key_prefix='email_boxes_for_user_{telegram_id}', schema=EmailBoxOutputSchema)
    async def get_email_boxes_for_user(telegram_id: int) -> list[EmailBoxOutputSchema]:
        """Сервисный слой получения списка почтовых ящиков пользователя через telegram_id"""
        try:
            email_boxes = await email_repo.get_all_boxes_for_user(telegram_id)
            return [EmailBoxOutputSchema.from_orm(box) for box in email_boxes]
        except ObjectDoesNotExist:
            raise EmailBoxesNotFoundError(f'No email boxes found for user with telegram_id: {telegram_id}')

    @staticmethod
    @cache_async(key_prefix='email_box_{telegram_id}_{email_username}', schema=EmailBoxOutputSchema)
    async def get_email_box_by_username_for_user(telegram_id: int, email_username: str) -> EmailBoxOutputSchema:
        """Сервисный слой получения почтового ящика через telegram_id и email_username"""

        email_box = await email_repo.get_by_email_username_for_user(telegram_id, email_username)
        if not email_box:
            raise EmailBoxByUsernameNotFoundError(
                f'No email box found with email_username: {email_username} for user with telegram_id: {telegram_id}')

        return EmailBoxOutputSchema.from_orm(email_box)

    @staticmethod
    async def stop_listening_for_email(telegram_id: int, email_username: str) -> dict[str, str]:
        email_box = await email_repo.get_by_email_username_for_user(telegram_id, email_username)
        if not email_box:
            raise EmailBoxByUsernameNotFoundError(
                f'No email box found with email_username: {email_username} for user with telegram_id: {telegram_id}')

        user_key = f'user:{email_username}'
        user_data_str = redis_client.get_key(user_key)
        if not user_data_str:
            raise UserDataNotFoundError(f'No data found for user {email_username}')

        await email_repo.set_listening_status(email_box.id, False)

        redis_client.delete_key(f'{CACHE_PREFIX}email_boxes_for_user_{telegram_id}')

        user_data = json.loads(user_data_str)
        if user_data['listening']:
            user_data['listening'] = False
            redis_client.set_key(user_key, json.dumps(user_data))
            return {'detail': f'Listening for {email_username} will be stopped in 2 minutes!'}
        raise EmailListeningError(f'Listening for {email_username} was not started!')

    @staticmethod
    async def start_listening_for_email(telegram_id: int, email_username: str) -> dict[str, str]:
        email_box = await email_repo.get_by_email_username_for_user(telegram_id, email_username)

        email_domain = await email_domain_repo.get_host_by_slug(email_box.email_service.slug)
        if not email_domain:
            raise EmailServiceSlugDoesNotExist(f'Email service with slug {email_box.email_service.slug} does not exist')

        user_key = f'user:{email_username}'
        user_data_str = redis_client.get_key(user_key)
        if not user_data_str:
            raise UserDataNotFoundError(f'No data found for user {email_username}')
        else:
            user_data = json.loads(user_data_str)
            if user_data['listening']:
                raise EmailAlreadyListeningError(f'Listening for {email_username} was already started!')

        listener = IMAPListener(
            host=email_domain.address,
            user=email_box.email_username,
            password=email_box.email_password,
            telegram_id=email_box.user_id.telegram_id,
            callback=process_email
        )

        await listener.start()

        await email_repo.set_listening_status(email_box.id, True)
        redis_client.delete_key(f'{CACHE_PREFIX}email_boxes_for_user_{telegram_id}')
        user_key = f'user:{email_box.email_username}'
        user_data = {
            'telegram_id': email_box.user_id.telegram_id,
            'email_username': email_box.email_username,
            'listening': True
        }

        try:
            redis_client.set_key(user_key, json.dumps(user_data))
        except Exception as e:
            logger.error(f'Error while setting key in Redis: {e}')
        return {'detail': f'Listening {email_box.email_username} was started!'}

    @staticmethod
    @cache_async(key_prefix='all_email_domains', schema=EmailServiceSchema, use_cache=False)
    async def get_all_domains() -> list[EmailServiceSchema]:
        """Сервисный слой получения списка всех доступных почтовых сервисов"""
        try:
            services = await email_repo.get_all_domains()
            return [EmailServiceSchema.from_orm(service) for service in services]

        except ObjectDoesNotExist:
            raise EmailServicesNotFoundError('No email services found')
