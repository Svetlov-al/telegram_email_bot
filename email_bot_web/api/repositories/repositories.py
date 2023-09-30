from email_service.models import BoxFilter, EmailBox, EmailService
from user.models import BotUser


class BotUserRepository:

    @staticmethod
    async def create(telegram_id: int) -> BotUser:
        """Создание пользователя"""

        return await BotUser.objects.acreate(telegram_id=telegram_id)

    @staticmethod
    async def get_by_telegram_id(telegram_id: int) -> BotUser:
        """Получение пользователя по telegram_id"""
        return await BotUser.objects.aget(telegram_id=telegram_id)

    @staticmethod
    async def get_all() -> list[BotUser]:
        """Получение списка всех пользователей"""

        return [user async for user in BotUser.objects.all()]


class EmailBoxRepository:

    @staticmethod
    async def create(user_id: int, email_service_slug: str, email_username: str, email_password: str) -> EmailBox:
        """Создание почтового ящика"""

        user = await BotUser.objects.aget(pk=user_id)
        email_service = await EmailService.objects.aget(slug=email_service_slug)

        return await EmailBox.objects.acreate(user_id=user,
                                              email_service=email_service,
                                              email_username=email_username,
                                              email_password=email_password)

    @staticmethod
    async def get_all_boxes_for_user(telegram_id: int) -> list[EmailBox]:
        """Получение всех почтовых ящиков пользователя с присоединенными данными"""

        email_boxes = [box async for box in
                       EmailBox.objects.select_related('email_service', 'user_id').prefetch_related('filters').filter(
                           user_id__telegram_id=telegram_id
                       )]

        return email_boxes

    @staticmethod
    async def get_all_boxes() -> list[EmailBox]:
        """Получение всех почтовых ящиков"""

        email_boxes = [box async for box in EmailBox.objects.select_related(
            'email_service', 'user_id').prefetch_related('filters').all()]
        return email_boxes

    @staticmethod
    async def get_by_email_username_for_user(telegram_id: int, email_username: str) -> EmailBox:
        """Получение конкретного почтового ящика со всеми фильтрами"""

        email_box = await EmailBox.objects.select_related('email_service', 'user_id').prefetch_related(
            'filters').filter(
            user_id__telegram_id=telegram_id,
            email_username=email_username
        ).afirst()

        return email_box

    @staticmethod
    async def get_services() -> list[EmailService]:
        """Получение списка всех доступных почтовых сервисов"""

        return [domen async for domen in EmailService.objects.all()]

    @staticmethod
    async def set_listening_status(email_box_id: int, status: bool) -> None:
        """Устанавливает статус прослушивания для EmailBox"""

        await EmailBox.objects.filter(id=email_box_id).aupdate(listening=status)


class BoxFilterRepository:

    @staticmethod
    async def create(email_box: EmailBox, filter_value: str, filter_name: str | None = None) -> BoxFilter:
        """Создание фильтра для определенного почтового ящика"""

        return await BoxFilter.objects.acreate(box_id=email_box, filter_value=filter_value, filter_name=filter_name)

    @staticmethod
    async def get_by_box_id(box_id: int) -> list[BoxFilter]:
        """Получение списка фильтров определенного почтового ящика"""

        return [filter_obj async for filter_obj in BoxFilter.objects.select_related('box_id').filter(box_id=box_id)]


class EmailServiceRepository:
    """Получение почтового сервиса"""

    @staticmethod
    async def get_host_by_slug(email_service_slug: str) -> EmailService:
        return await EmailService.objects.aget(slug=email_service_slug)
