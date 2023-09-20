from api.repositories.repositories import BotUserRepository
from api.services.exceptions import UserAlreadyExistsError, UserNotFoundError
from django.db import IntegrityError
from user.models import BotUser

user_repo = BotUserRepository


class BotUserService:

    @staticmethod
    async def create_bot_user(telegram_id: int) -> BotUser:
        try:
            return await user_repo.create(telegram_id)
        except IntegrityError:
            raise UserAlreadyExistsError(f'User with telegram_id {telegram_id} already exists.')

    @staticmethod
    async def get_bot_user(telegram_id: int) -> BotUser | None:
        try:
            user = await user_repo.get_by_telegram_id(telegram_id)
            return user
        except BotUser.DoesNotExist:
            raise UserNotFoundError(f'User with telegram_id {telegram_id} not found.')
