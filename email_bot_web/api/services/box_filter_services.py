from api.repositories.repositories import BoxFilterRepository, EmailBoxRepository
from api.services.exceptions import BoxFilterCreationError, BoxFiltersNotFoundError
from django.core.exceptions import ObjectDoesNotExist
from email_domain.models import BoxFilter
from email_domain.schema import BoxFilterSchema
from ninja.errors import ValidationError

box_filter_repo = BoxFilterRepository
email_repo = EmailBoxRepository


class BoxFilterService:

    @staticmethod
    async def create_box_filter(email_box, filter_value: str, filter_name: str | None = None) -> BoxFilter:
        try:
            return await box_filter_repo.create(email_box, filter_value, filter_name)
        except (ObjectDoesNotExist, ValidationError) as e:
            raise BoxFilterCreationError(f'Error creating filter for box: {str(e)}')

    @staticmethod
    async def get_filters_for_user_and_email(telegram_id: int, email_username: str) -> list[BoxFilterSchema]:
        email_box = await email_repo.get_by_email_username_for_user(telegram_id, email_username)
        if not email_box:
            raise BoxFiltersNotFoundError(
                f'No email box found for user with telegram_id: {telegram_id} and email_username: {email_username}')

        filters_obj = await box_filter_repo.get_by_box_id(email_box.id)
        return [BoxFilterSchema.from_orm(filter_obj) for filter_obj in filters_obj]
