from email_service.models import BoxFilter, EmailBox, EmailService
from ninja import Schema
from user.models import BotUser


class BotUserCreateSchema(Schema):
    """Схема создания пользователя"""
    telegram_id: int

    class Config:
        model = BotUser
        orm_mode = True


class EmailServiceSchema(Schema):
    """Схема для модели EmailService"""
    title: str
    slug: str
    address: str
    port: int

    class Config:
        model = EmailService
        orm_mode = True


class BoxFilterSchema(Schema):
    """Схема для модели BoxFilter"""
    filter_value: str
    filter_name: str | None = None

    class Config:
        model = BoxFilter
        orm_mode = True


class EmailBoxCreateSchema(Schema):
    """Схема для создания EmailBox"""
    user_id: int
    email_service: int
    email_username: str
    email_password: str
    filters: list[BoxFilterSchema]

    class Config:
        model = EmailBox
        orm_mode = True


class EmailBoxOutputSchema(Schema):
    """Схема для просмотра EmailBox"""
    user_id: int
    email_service: EmailServiceSchema
    email_username: str
    filters: list[BoxFilterSchema]

    class Config:
        model = EmailBox
        orm_mode = True
