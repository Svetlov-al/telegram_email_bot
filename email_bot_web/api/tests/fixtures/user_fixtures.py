from typing import Callable, TypedDict

import pytest
from factory import Sequence
from factory.django import DjangoModelFactory
from user.models import BotUser


class BotUserFactory(DjangoModelFactory):
    class Meta:
        model = BotUser
        django_get_or_create = ('telegram_id',)

    telegram_id = Sequence(lambda n: n)
    is_active = True


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def create_bot_user() -> Callable[[int], BotUser]:
    def make_bot_user(telegram_id: int):
        return BotUserFactory(telegram_id=telegram_id)
    return make_bot_user


@pytest.fixture
def test_user_data() -> dict[str, str | int]:
    return {
        'telegram_id': 123456,
        'email_username': 'example@example.com',
        'content_type': 'application/json'
    }


class UserData(TypedDict):
    """
    UserData TypedDict.

    Описывает структуру данных пользователя, которая включает в себя:
    - telegram_id: Уникальный идентификатор пользователя в Telegram.
    - email_username: Имя пользователя для электронной почты.
    - content_type: Тип содержимого, который используется при отправке данных.

    Пример использования:
    user_data = UserData(
        telegram_id=123456,
        email_username="example@example.com",
        content_type="application/json"
    )
    """

    telegram_id: int
    email_username: str
    content_type: str


class CreateBotUserArgs(TypedDict):
    telegram_id: int
