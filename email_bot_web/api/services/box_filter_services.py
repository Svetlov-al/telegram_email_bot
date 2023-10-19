from api.repositories.repositories import BoxFilterRepository, EmailBoxRepository
from django.core.exceptions import ObjectDoesNotExist
from email_service.models import BoxFilter
from email_service.schema import BoxFilterSchema
from infrastructure.exceptions import (
    BoxFilterCreationError,
    BoxFiltersNotFoundError,
    EmailBoxByUsernameNotFoundError,
)
from infrastructure.tools import CACHE_PREFIX, cache_async, redis_client
from ninja.errors import ValidationError

box_filter_repo = BoxFilterRepository
email_repo = EmailBoxRepository


class BoxFilterService:

    @staticmethod
    async def create_box_filter(telegram_id: int, email_username: str, filter_value: str, filter_name: str | None = None) -> BoxFilter:
        """Создает фильтр для почтового ящика"""

        try:
            email_box = await email_repo.get_by_email_username_for_user(telegram_id, email_username)
            filter_obj = await box_filter_repo.create(email_box, filter_value, filter_name)

            user_key_email = f'{CACHE_PREFIX}email_box_{telegram_id}_{email_username}'
            user_key_filters = f'{CACHE_PREFIX}filters_for_{email_box.user_id.telegram_id}_{email_box.email_username}'
            redis_client.delete_key(user_key_filters)
            redis_client.delete_key(user_key_email)

            return filter_obj
        except ValidationError as e:
            raise BoxFilterCreationError(f'Error creating filter for box: {str(e)}')
        except ObjectDoesNotExist:
            raise EmailBoxByUsernameNotFoundError(f'No email boxes found for user with telegram_id: {telegram_id}')

    @staticmethod
    @cache_async(key_prefix='filters_for_{telegram_id}_{email_username}', schema=BoxFilterSchema)
    async def get_filters_for_user_and_email(telegram_id: int, email_username: str) -> list[BoxFilterSchema]:
        """Возвращает список фильтров у пользователя по конкретному почтовому ящику"""

        email_box = await email_repo.get_by_email_username_for_user(telegram_id, email_username)
        if not email_box:
            raise BoxFiltersNotFoundError(
                f'No email box found for user with telegram_id: {telegram_id} and email_username: {email_username}')

        filters_obj = await box_filter_repo.get_by_box_id(email_box.id)
        return [BoxFilterSchema.from_orm(filter_obj) for filter_obj in filters_obj]
