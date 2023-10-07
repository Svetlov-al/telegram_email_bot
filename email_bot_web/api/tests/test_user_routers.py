import json
from typing import Callable

import pytest
from api.tests.fixtures.email_fixtures import EmailBoxData, EmailServiceFactory
from api.tests.fixtures.user_fixtures import UserData
from email_service.models import BoxFilter, EmailBox
from rest_framework.test import APIClient
from user.models import BotUser

BASE_URL = '/api/v1/users'


class TestUser:
    """Класс для тестирования блока связанного с пользователями."""

    @pytest.mark.django_db
    def test_user_creation(self, create_bot_user: Callable[[int], BotUser],
                           test_user_data: UserData
                           ) -> None:
        """Тест фикстуры что создает пользователя в базе"""

        user = create_bot_user(test_user_data['telegram_id'])
        assert user.telegram_id == test_user_data['telegram_id']

    @pytest.mark.django_db
    def test_create_user(self, api_client: APIClient,
                         test_user_data: UserData
                         ) -> None:
        """Тест создания пользоваля."""

        response = api_client.post(BASE_URL,
                                   json.dumps({'telegram_id': test_user_data['telegram_id']}),
                                   content_type='application/json')

        assert response.status_code == 201
        assert response.json()['telegram_id'] == test_user_data['telegram_id']

    @pytest.mark.django_db
    def test_get_user(self, api_client: APIClient,
                      create_bot_user: Callable[[int], BotUser],
                      test_user_data: UserData) -> None:
        """Тест получения пользователя."""

        user = create_bot_user(test_user_data['telegram_id'])

        url = f'{BASE_URL}/{user.telegram_id}'
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.json()['telegram_id'] == user.telegram_id

    @pytest.mark.django_db
    def test_get_does_not_exist_user(self, api_client: APIClient,
                                     test_user_data: UserData
                                     ) -> None:
        """Тест получения несуществующего пользователя."""

        url = f"{BASE_URL}/{test_user_data['telegram_id']}"
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.json()['detail'] == f"User with telegram_id {test_user_data['telegram_id']} not found."

    @pytest.mark.django_db
    def test_create_already_exist_user(self, api_client: APIClient,
                                       test_user_data: UserData,
                                       create_bot_user: Callable[[int], BotUser]
                                       ) -> None:
        """Тест создания пользователя с неверными данными."""

        user = create_bot_user(test_user_data['telegram_id'])
        response = api_client.post(BASE_URL,
                                   json.dumps({'telegram_id': user.telegram_id}),
                                   content_type='application/json')
        assert response.status_code == 400
        assert response.json() == {'detail': f'User with telegram_id {user.telegram_id} already exists.'}

    @pytest.mark.django_db
    def test_user_without_boxes_and_filters(self,
                                            api_client: APIClient,
                                            create_bot_user: Callable[[int], BotUser],
                                            test_user_data: UserData
                                            ) -> None:
        """Тест получения списка всех почтовых ящиков и фильтров пользователя."""

        user = create_bot_user(test_user_data['telegram_id'])
        response = api_client.get(f'{BASE_URL}/{user.telegram_id}/boxes')

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.django_db
    def test_user_with_boxes_and_filters(
            self,
            api_client: APIClient,
            create_bot_user: Callable[[int], BotUser],
            create_email_box: Callable[..., EmailBox],
            create_box_filter: Callable[..., BoxFilter],
            test_user_data: UserData,
            test_email_data: EmailBoxData
    ) -> None:
        """Тест получения списка всех почтовых ящиков и фильтров пользователя."""

        user = create_bot_user(test_user_data['telegram_id'])

        email_service = EmailServiceFactory(slug='some_service_slug')

        box_data = {
            'user_id': user,
            'email_service': email_service,
            'email_username': test_email_data['email_username'],
            'email_password': test_email_data['email_password'],
        }

        email_box = create_email_box(**box_data)

        filter_data = {
            'box_id': email_box,
            'filter_value': 'some_filter_value',
            'filter_name': 'some_filter_name'
        }
        box_filter = create_box_filter(**filter_data)

        response = api_client.get(f'{BASE_URL}/{user.telegram_id}/boxes')
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]['filters'][0]['filter_value'] == box_filter.filter_value
