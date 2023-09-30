import json

from api.repositories.repositories import BoxFilterRepository, EmailBoxRepository
from api.services.exceptions import (
    BoxFilterCreationError,
    BoxFiltersNotFoundError,
    EmailBoxByUsernameNotFoundError,
)
from api.services.tools import RedisTools
from django.core.exceptions import ObjectDoesNotExist
from email_service.models import BoxFilter
from email_service.schema import BoxFilterSchema
from ninja.errors import ValidationError

box_filter_repo = BoxFilterRepository
email_repo = EmailBoxRepository

redis_client = RedisTools()


class BoxFilterService:

    @staticmethod
    async def create_box_filter(telegram_id: int, email_username: str, filter_value: str, filter_name: str | None = None) -> BoxFilter:
        try:
            email_box = await email_repo.get_by_email_username_for_user(telegram_id, email_username)
            filter_obj = await box_filter_repo.create(email_box, filter_value, filter_name)

            await redis_client.delete_key(f'filters_for_{email_box.user_id}_{email_box.email_username}')

            return filter_obj
        except ValidationError as e:
            raise BoxFilterCreationError(f'Error creating filter for box: {str(e)}')
        except ObjectDoesNotExist:
            raise EmailBoxByUsernameNotFoundError(f'No email boxes found for user with telegram_id: {telegram_id}')

    @staticmethod
    async def get_filters_for_user_and_email(telegram_id: int, email_username: str) -> list[BoxFilterSchema]:
        cached_data_str = await redis_client.get_key(f'filters_for_{telegram_id}_{email_username}')
        if cached_data_str:
            cached_data = json.loads(cached_data_str)
            return [BoxFilterSchema(**item) for item in cached_data]

        email_box = await email_repo.get_by_email_username_for_user(telegram_id, email_username)
        if not email_box:
            raise BoxFiltersNotFoundError(
                f'No email box found for user with telegram_id: {telegram_id} and email_username: {email_username}')

        filters_obj = await box_filter_repo.get_by_box_id(email_box.id)
        filters_schemas = [BoxFilterSchema.from_orm(filter_obj) for filter_obj in filters_obj]

        filters_schemas_serialized = json.dumps([filter_schema.dict() for filter_schema in filters_schemas])
        await redis_client.set_key(f'filters_for_{telegram_id}_{email_username}', filters_schemas_serialized)

        return filters_schemas
