import json
from typing import Callable

import pytest
from email_service.models import EmailBox, EmailService
from rest_framework.test import APIClient
from user.models import BotUser

BASE_URL = '/api/v1/emailboxes'


class TestEmails:
    """Класс для тестирования блока связанного с почтовыми ящиками"""

    @pytest.mark.django_db
    def test_all_domains(self, api_client: APIClient
                         ) -> None:
        """Тест получения пустого списка доступных доменов."""

        response = api_client.get(f'{BASE_URL}/services')

        assert response.json() == []

    @pytest.mark.django_db
    def test_not_empty_all_domains(self, api_client: APIClient, create_email_service: Callable[[], EmailService]
                                   ) -> None:
        """Тест получения списка доступных доментов"""

        domain = create_email_service()

        response = api_client.get(f'{BASE_URL}/services')
        response_data = response.json()

        assert response.status_code == 200
        assert len(response_data) == 1
        assert response_data[0]['title'] == domain.title

    @pytest.mark.django_db
    def test_create_already_exist_emailbox_with_filters(self, api_client: APIClient,
                                                        create_email_box: Callable[..., EmailBox],
                                                        test_filter_data: dict[str, str]
                                                        ) -> None:
        """Тест создания уже существующего почтового ящика."""

        email_box = create_email_box()
        email_box_data = {
            'user_id': email_box.user_id.telegram_id,
            'email_service_slug': email_box.email_service.slug,
            'email_username': email_box.email_username,
            'email_password': email_box.email_password,
            'filters': [test_filter_data]
        }

        response = api_client.post(f'{BASE_URL}', json.dumps(email_box_data), content_type='application/json')
        assert response.status_code == 400
        assert response.json()['detail'] == (f'Email box with username {email_box_data["email_username"]} '
                                             f'already exists for user {email_box.user_id.telegram_id}')

    @pytest.mark.django_db
    def test_create_emailbox_with_nonexistent_service(self,
                                                      api_client: APIClient,
                                                      create_bot_user: Callable[[int], BotUser],
                                                      test_user_data: dict[str, int],
                                                      test_email_data: dict[str, str],
                                                      test_filter_data: dict[str, str]):
        """Тест проверки создания почтового ящика с использованием несуществующего "Email Domain"
        """
        user = create_bot_user(test_user_data['telegram_id'])
        nonexistent_service_slug = 'nonexistent-service-slug'
        email_box_data = {
            'user_id': user.telegram_id,
            'email_service_slug': nonexistent_service_slug,
            'email_username': test_email_data['email_username'],
            'email_password': test_email_data['email_password'],
            'filters': [test_filter_data]
        }

        response = api_client.post(f'{BASE_URL}', json.dumps(email_box_data), content_type='application/json')
        assert response.status_code == 404
        assert response.json()['detail'] == f'Email service with slug {nonexistent_service_slug} does not exist'

    @pytest.mark.django_db
    def test_create_emailbox_with_invalid_credentials(self, api_client: APIClient,
                                                      create_bot_user: Callable[[int], BotUser],
                                                      create_email_service: Callable[..., EmailService],
                                                      test_user_data: dict[str, int],
                                                      test_email_data: dict[str, str],
                                                      test_filter_data: dict[str, str]
                                                      ) -> None:
        """Тест проверки корректности предоставленных данных для прослушивания почты."""

        user = create_bot_user(test_user_data['telegram_id'])

        email_service = create_email_service(slug='google')

        invalid_email_data = test_email_data
        invalid_email_data['email_password'] = 'wrong_password'

        email_box_data = {
            'user_id': user.telegram_id,
            'email_service_slug': email_service.slug,
            'email_username': invalid_email_data['email_username'],
            'email_password': invalid_email_data['email_password'],
            'filters': [test_filter_data]
        }

        response = api_client.post(f'{BASE_URL}', json.dumps(email_box_data), content_type='application/json')

        assert response.status_code == 400
        assert response.json()['detail'] == 'Error with authorisation, check email or password!'

    @pytest.mark.django_db
    def test_create_email_box_with_invalid_data(self, api_client: APIClient,
                                                create_bot_user: Callable[[int], BotUser],
                                                create_email_service: Callable[..., EmailService],
                                                test_user_data: dict[str, int],
                                                test_email_data: dict[str, str],
                                                test_filter_data: dict[str, str]
                                                ) -> None:
        """Тест создания почтового ящика с невалидными данными."""

        user = create_bot_user(test_user_data['telegram_id'])
        email_service = create_email_service(slug='google')
        email_box_data = {
            'user_id': user.telegram_id,
            'email_service_slug': email_service.slug,
            'email_username': 'ivalid_email_username',
            'email_password': test_email_data['email_password'],
            'filters': [test_filter_data]
        }

        response = api_client.post(f'{BASE_URL}', json.dumps(email_box_data), content_type='application/json')
        assert response.status_code == 400
        assert response.json()[
            'detail'] == "Error creating email box with filters: ['Invalid email_username provided.']"

    @pytest.mark.django_db
    def test_get_emailbox_by_username_for_user(self, api_client: APIClient, create_email_box: Callable[..., EmailBox],
                                               ) -> None:
        """Тест получения информации о почтовом ящике по username для конкретного пользователя."""

        email_box = create_email_box()

        response = api_client.post(f'{BASE_URL}/info', json.dumps({
            'telegram_id': email_box.user_id.telegram_id,
            'email_username': email_box.email_username
        }), content_type='application/json')

        assert response.status_code == 200
        assert len(response.json()) == 5
        assert response.json()['email_username'] == email_box.email_username
