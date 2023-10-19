from api.repositories.repositories import BotUserRepository
from infrastructure.exceptions import UserAlreadyExistsError, UserNotFoundError
from user.models import BotUser

user_repo = BotUserRepository


class BotUserService:

    @staticmethod
    async def create_bot_user(telegram_id: int) -> BotUser:
        """Создает пользователя"""

        try:
            await user_repo.get_by_telegram_id(telegram_id)
            raise UserAlreadyExistsError(f'User with telegram_id {telegram_id} already exists.')
        except BotUser.DoesNotExist:
            user = await user_repo.create(telegram_id)
            return user

    @staticmethod
    async def get_bot_user(telegram_id: int) -> BotUser | None:
        """Получает объект пользователя"""

        try:
            user = await user_repo.get_by_telegram_id(telegram_id)
            return user
        except BotUser.DoesNotExist:
            raise UserNotFoundError(f'User with telegram_id {telegram_id} not found.')
