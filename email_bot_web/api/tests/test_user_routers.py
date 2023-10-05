import json
from typing import Callable

import pytest
from rest_framework.test import APIClient

BASE_URL = '/api/v1/users'


class TestUser:
    """Класс для тестирования блока связанного с пользователями"""

    @pytest.mark.django_db
    def test_user_creation(self, create_bot_user: Callable, test_user_data: dict) -> None:
        """Тест фикстуры что создает пользователя в базе"""

        user = create_bot_user(telegram_id=test_user_data['telegram_id'])
        assert user.telegram_id == test_user_data['telegram_id']

    @pytest.mark.django_db
    def test_create_user(self, api_client: APIClient, test_user_data: dict) -> None:
        """Тест создания пользоваля."""

        response = api_client.post(BASE_URL,
                                   json.dumps({'telegram_id': test_user_data['telegram_id']}),
                                   content_type='application/json')

        assert response.status_code == 201
        assert response.json()['telegram_id'] == test_user_data['telegram_id']

    @pytest.mark.django_db
    def test_get_user(self, api_client: APIClient, create_bot_user: Callable, test_user_data: dict) -> None:
        """Тест получения пользователя."""

        user = create_bot_user(telegram_id=test_user_data['telegram_id'])

        url = f'{BASE_URL}/{user.telegram_id}'
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.json()['telegram_id'] == user.telegram_id

    @pytest.mark.django_db
    def test_get_does_not_exist_user(self, api_client: APIClient, test_user_data: dict) -> None:
        """Тест получения несуществующего пользователя."""

        url = f"{BASE_URL}/{test_user_data['telegram_id']}"
        response = api_client.get(url)

        assert response.status_code == 404
        assert response.json() == {'detail': f"User with telegram_id {test_user_data['telegram_id']} not found."}

    @pytest.mark.django_db
    def test_create_already_exist_user(self, api_client: APIClient,
                                       test_user_data: dict, create_bot_user: Callable) -> None:
        """Тест создания пользователя с неверными данными."""

        user = create_bot_user(telegram_id=test_user_data['telegram_id'])
        response = api_client.post(BASE_URL,
                                   json.dumps({'telegram_id': user.telegram_id}),
                                   content_type='application/json')
        assert response.status_code == 400
        assert response.json() == {'detail': f'User with telegram_id {user.telegram_id} already exists.'}

    @pytest.mark.django_db
    def test_user_with_boxes_and_filters(self, api_client: APIClient,
                                         create_bot_user: Callable, test_user_data: dict) -> None:
        """Тест получения списка всех почтовых ящиков и фильтров пользователя."""
        user = create_bot_user(telegram_id=test_user_data['telegram_id'])
        response = api_client.get(f'{BASE_URL}/{user.telegram_id}/boxes')

        assert response.status_code == 200
        assert response.json() == []
