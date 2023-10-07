from typing import TypedDict

import pytest
from api.tests.fixtures.user_fixtures import BotUserFactory
from email_service.models import EmailBox, EmailService
from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory
from rest_framework.test import APIClient
from user.models import BotUser

BASE_URL = '/api/v1/emailboxes'


class EmailServiceFactory(DjangoModelFactory):
    class Meta:
        model = EmailService

    title = Sequence(lambda n: f'Service {n}')
    slug = Sequence(lambda n: f'service-{n}')
    address = 'smtp.example.com'
    port = 587


class EmailBoxFactory(DjangoModelFactory):
    class Meta:
        model = EmailBox

    user_id = SubFactory(BotUserFactory)
    email_service = SubFactory(EmailServiceFactory)
    email_username = Sequence(lambda n: f'user{n}@example.com')
    email_password = 'password'
    listening = True


@pytest.fixture
def create_email_box(create_bot_user, create_email_service):
    def make_email_box(**kwargs):
        return EmailBoxFactory(**kwargs)
    return make_email_box


@pytest.fixture
def create_email_service():
    def make_email_service(**kwargs):
        return EmailServiceFactory(**kwargs)
    return make_email_service


@pytest.fixture
def test_email_data():
    return {
        'email_username': 'user@example.com',
        'email_password': 'password123'
    }


@pytest.fixture(autouse=True)
def clear_decorator_cache_after_test():
    client = APIClient()
    yield
    response = client.post(f'{BASE_URL}/clear_decorator_cache')
    assert response.status_code == 200
    assert response.json()['detail'] == 'Cache cleared'


class EmailBoxData(TypedDict):
    """
    EmailBoxData TypedDict.

    Описывает структуру данных для почтового ящика, которая включает в себя:
    - user_id: Ссылка на объект пользователя (BotUser), которому принадлежит почтовый ящик.
    - email_service: Ссылка на объект сервиса электронной почты (EmailService), который используется для этого ящика.
    - email_username: Имя пользователя или адрес электронной почты, используемый для входа в почтовый ящик.
    - email_password: Пароль, используемый для входа в почтовый ящик.

    Пример использования:
    email_box_data = EmailBoxData(
        user_id=bot_user_instance,
        email_service=email_service_instance,
        email_username="user@example.com",
        email_password="password123"
    )
    """

    user_id: BotUser
    email_service: EmailService
    email_username: str
    email_password: str
