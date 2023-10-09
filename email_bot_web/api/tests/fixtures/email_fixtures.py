from typing import Callable

import pytest
from api.tests.fixtures.user_fixtures import BotUserFactory
from django.test import Client
from email_service.models import EmailBox, EmailService
from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory

BASE_URL = '/api/v1/emailboxes'


class EmailServiceFactory(DjangoModelFactory):
    class Meta:
        model = EmailService

    title = Sequence(lambda n: f'Service {n}')
    slug = Sequence(lambda n: f'service-{n}')
    address = 'imap.gmail.com'
    port = 993


class EmailBoxFactory(DjangoModelFactory):
    class Meta:
        model = EmailBox

    user_id = SubFactory(BotUserFactory)
    email_service = SubFactory(EmailServiceFactory)
    email_username = Sequence(lambda n: f'user{n}@example.com')
    email_password = 'password'
    listening = True


@pytest.fixture
def create_email_box(create_bot_user, create_email_service) -> Callable:
    def make_email_box(**kwargs) -> EmailBox:
        return EmailBoxFactory(**kwargs)

    return make_email_box


@pytest.fixture
def create_email_service() -> Callable:
    def make_email_service(**kwargs) -> EmailService:
        return EmailServiceFactory(**kwargs)

    return make_email_service


@pytest.fixture
def test_email_data() -> dict[str, str]:
    return {
        'email_username': 'user@example.com',
        'email_password': 'password123',
    }


@pytest.fixture(autouse=True)
def clear_decorator_cache_after_test():
    client = Client()
    yield
    response = client.post(f'{BASE_URL}/clear_decorator_cache')
    assert response.status_code == 200
    assert response.json()['detail'] == 'Cache cleared'
