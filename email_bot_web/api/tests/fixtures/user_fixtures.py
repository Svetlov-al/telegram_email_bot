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
        'email_username': 'example@example.com'
    }
