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
from django.core.exceptions import ObjectDoesNotExist, ValidationError
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
            return await email_repo.create(data.user_id, data.email_service_slug, data.email_username, data.email_password)
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
            return email_box
        except (ObjectDoesNotExist, ValidationError) as e:
            raise EmailBoxWithFiltersCreationError(f'Error creating email box with filters: {e}')

    @staticmethod
    async def get_email_boxes_for_user(telegram_id: int) -> list[EmailBoxOutputSchema]:
        try:
            email_boxes = await email_repo.get_all_boxes_for_user(telegram_id)
            email_boxes_schemas = [EmailBoxOutputSchema.from_orm(box) for box in email_boxes]
            return email_boxes_schemas
        except ObjectDoesNotExist:
            raise EmailBoxesNotFoundError(f'No email boxes found for user with telegram_id: {telegram_id}')

    @staticmethod
    async def get_email_box_by_username_for_user(telegram_id: int, email_username: str) -> EmailBox:
        email_box = await email_repo.get_by_email_username_for_user(telegram_id, email_username)
        if not email_box:
            raise EmailBoxByUsernameNotFoundError(
                f'No email box found with email_username: {email_username} for user with telegram_id: {telegram_id}')
        return email_box

    @staticmethod
    async def get_all_services() -> list[EmailServiceSchema]:
        try:
            services = await email_repo.get_services()
            return [EmailServiceSchema.from_orm(service) for service in services]
        except ObjectDoesNotExist:
            raise EmailServicesNotFoundError('No email services found')
