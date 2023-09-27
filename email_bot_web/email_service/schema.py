from email_service.models import BoxFilter, EmailBox, EmailService
from ninja import Schema


class BotUserCreateSchema(Schema):
    """Схема создания пользователя"""

    telegram_id: int


class BotUserOutSchema(BotUserCreateSchema):
    """Схема вывода информации о пользвателе"""
    pass


class EmailBoxRequestSchema(Schema):
    """Схема валидации входных данных для поиска
    конкретного почтового ящика"""

    telegram_id: int
    email_username: str


class EmailServiceSchema(Schema):
    """Схема для модели EmailService"""

    title: str
    slug: str
    address: str
    port: int

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj: EmailService) -> 'EmailServiceSchema':
        return cls(
            title=obj.title,
            slug=obj.slug,
            address=obj.address,
            port=obj.port
        )


class BoxFilterSchema(Schema):
    """Схема для модели BoxFilter"""

    filter_value: str
    filter_name: str | None = None

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj: BoxFilter) -> 'BoxFilterSchema':
        return cls(
            filter_value=obj.filter_value,
            filter_name=obj.filter_name
        )


class CreateBoxFilterRequest(Schema):
    telegram_id: int
    email_username: str
    filter_data: BoxFilterSchema


class EmailBoxCreateSchema(Schema):
    """Схема для создания EmailBox"""

    user_id: int
    email_service_slug: str
    email_username: str
    email_password: str
    filters: list[BoxFilterSchema]

    class Config:
        orm_mode = True


class EmailBoxOutputSchema(Schema):
    """Схема для просмотра EmailBox"""

    user_id: int
    email_service: EmailServiceSchema
    email_username: str
    filters: list[BoxFilterSchema]

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj: EmailBox) -> 'EmailBoxOutputSchema':
        return cls(
            user_id=obj.user_id.telegram_id,
            email_service=EmailServiceSchema.from_orm(obj.email_service),
            email_username=obj.email_username,
            filters=[BoxFilterSchema.from_orm(filter_obj) for filter_obj in obj.filters.all()]
        )


class ErrorSchema(Schema):
    """Схема обработки ошибок"""

    detail: str


class ImapEmailModel(Schema):
    """Схема создания объекта письма"""

    subject: str
    from_: str
    to: str
    date: str
    body: str
