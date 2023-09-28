import json

from api.repositories.repositories import BoxFilterRepository, EmailBoxRepository
from api.services.exceptions import (
    EmailBoxByUsernameNotFoundError,
    EmailBoxCreationError,
    EmailBoxesNotFoundError,
    EmailBoxWithFiltersAlreadyExist,
    EmailBoxWithFiltersCreationError,
    EmailServicesNotFoundError,
)
from api.services.tasks import IMAP_SERVERS, IMAPListener, process_email
from api.services.tools import redis_client
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.serializers import serialize
from email_service.models import EmailBox
from email_service.schema import (
    EmailBoxCreateSchema,
    EmailBoxOutputSchema,
    EmailServiceSchema,
)

email_repo = EmailBoxRepository
box_filter_repo = BoxFilterRepository


class EmailBoxService:

    @staticmethod
    async def create_email_box(data: EmailBoxCreateSchema):
        try:
            result = await email_repo.create(data.user_id, data.email_service_slug, data.email_username,
                                             data.email_password)

            redis_client.delete_key(f'email_boxes_for_user_{data.user_id}')

            return result
        except (ObjectDoesNotExist, ValidationError) as e:
            raise EmailBoxCreationError(f'Error creating email box: {str(e)}')

    @staticmethod
    async def create_email_box_with_filters(data: EmailBoxCreateSchema) -> EmailBox:
        try:
            email_box = await email_repo.get_by_email_username_for_user(data.user_id, data.email_username)
            if email_box:
                raise EmailBoxWithFiltersAlreadyExist(
                    f'Email box with username {data.email_username} already exists for user {data.user_id}')

            email_box = await email_repo.create(data.user_id, data.email_service_slug,
                                                data.email_username, data.email_password)

            host = IMAP_SERVERS[data.email_service_slug]

            listener = IMAPListener(host=host, user=data.email_username,
                                    password=data.email_password, callback=process_email)
            await listener.start()

            for filter_data in data.filters:
                await box_filter_repo.create(email_box, filter_data.filter_value, filter_data.filter_name)

            redis_client.delete_key(f'email_boxes_for_user_{data.user_id}')

            return email_box
        except (ObjectDoesNotExist, ValidationError) as e:
            raise EmailBoxWithFiltersCreationError(f'Error creating email box with filters: {e}')

    @staticmethod
    async def get_email_boxes_for_user(telegram_id: int) -> list[EmailBoxOutputSchema]:
        """Сервисный слой получения списка почтовых ящиков пользователя через telegram_id"""

        cached_data_str = redis_client.get_key(f'email_boxes_for_user_{telegram_id}')
        if cached_data_str:
            cached_data = json.loads(cached_data_str)
            return [EmailBoxOutputSchema(**item) for item in cached_data]

        try:
            email_boxes = await email_repo.get_all_boxes_for_user(telegram_id)
            email_boxes_schemas = [EmailBoxOutputSchema.from_orm(box) for box in email_boxes]

            email_boxes_schemas_serialized = json.dumps([box.dict() for box in email_boxes_schemas])
            redis_client.set_key(f'email_boxes_for_user_{telegram_id}', email_boxes_schemas_serialized)

            return email_boxes_schemas
        except ObjectDoesNotExist:
            raise EmailBoxesNotFoundError(f'No email boxes found for user with telegram_id: {telegram_id}')

    @staticmethod
    async def get_email_box_by_username_for_user(telegram_id: int, email_username: str) -> EmailBox:
        """Сервисный слой получения почтового ящика через telegram_id и email_username"""

        cached_data_str = redis_client.get_key(f'email_box_{telegram_id}_{email_username}')
        if cached_data_str:
            cached_data = json.loads(cached_data_str)
            return EmailBox(**cached_data)

        email_box = await email_repo.get_by_email_username_for_user(telegram_id, email_username)
        if not email_box:
            raise EmailBoxByUsernameNotFoundError(
                f'No email box found with email_username: {email_username} for user with telegram_id: {telegram_id}')

        email_box_serialized = serialize('json', [email_box])
        redis_client.set_key(f'email_box_{telegram_id}_{email_username}', email_box_serialized)

        return email_box

    @staticmethod
    async def get_all_services() -> list[EmailServiceSchema]:
        """Сервисный слой получения списка всех доступных почтовых сервисов"""

        cached_data_str = redis_client.get_key('all_email_services')
        if cached_data_str:
            cached_data = json.loads(cached_data_str)
            return [EmailServiceSchema(**service) for service in cached_data]
        try:
            services = await email_repo.get_services()
            services_schemas = [EmailServiceSchema.from_orm(service) for service in services]

            services_schemas_serialized = json.dumps([service.dict() for service in services_schemas])
            redis_client.set_key('all_email_services', services_schemas_serialized)

            return services_schemas
        except ObjectDoesNotExist:
            raise EmailServicesNotFoundError('No email services found')
