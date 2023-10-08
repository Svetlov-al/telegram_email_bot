import json
from typing import Callable

import pytest
from api.tests.fixtures.email_fixtures import EmailServiceFactory
from email_service.models import BoxFilter, EmailBox
from rest_framework.test import APIClient
from user.models import BotUser

BASE_URL = '/api/v1/users'


class TestUser:
    """Класс для тестирования блока связанного с пользователями."""

    @pytest.mark.django_db
    def test_user_creation(self, create_bot_user: Callable[[int], BotUser],
                           test_user_data: dict[str, int]
                           ) -> None:
        """Тест фикстуры что создает пользователя в базе"""

        user = create_bot_user(test_user_data['telegram_id'])
        assert user.telegram_id == test_user_data['telegram_id']

    @pytest.mark.django_db
    def test_create_user(self, api_client: APIClient,
                         test_user_data: dict[str, int]
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
                      test_user_data: dict[str, int]) -> None:
        """Тест получения пользователя."""

        user = create_bot_user(test_user_data['telegram_id'])

        url = f'{BASE_URL}/{user.telegram_id}'
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.json()['telegram_id'] == user.telegram_id

    @pytest.mark.django_db
    def test_get_does_not_exist_user(self, api_client: APIClient,
                                     test_user_data: dict[str, int]
                                     ) -> None:
        """Тест получения несуществующего пользователя."""

        response = api_client.get(f"{BASE_URL}/{test_user_data['telegram_id']}")

        assert response.status_code == 404
        assert response.json()['detail'] == f"User with telegram_id {test_user_data['telegram_id']} not found."

    @pytest.mark.django_db
    def test_create_already_exist_user(self, api_client: APIClient,
                                       test_user_data: dict[str, int],
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
    def test_user_without_boxes_and_filters(self, api_client: APIClient, create_bot_user: Callable[[int], BotUser],
                                            test_user_data: dict[str, int]
                                            ) -> None:
        """Тест получения списка всех почтовых ящиков и фильтров пользователя."""

        user = create_bot_user(test_user_data['telegram_id'])
        response = api_client.get(f'{BASE_URL}/{user.telegram_id}/boxes')

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.django_db
    def test_user_with_boxes_and_filters(self, api_client: APIClient, create_box_filter: Callable[..., BoxFilter],
                                         ) -> None:
        """Тест получения списка всех почтовых ящиков и фильтров пользователя."""

        box_filter = create_box_filter()

        response = api_client.get(f'{BASE_URL}/{box_filter.box_id.user_id.telegram_id}/boxes')

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]['filters'][0]['filter_value'] == box_filter.filter_value
