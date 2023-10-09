import json
from typing import Callable

import pytest
from email_service.models import BoxFilter, EmailBox
from rest_framework.test import APIClient
from user.models import BotUser

BASE_URL = '/api/v1/filters'


class TestFilters:
    """Класс для тестирования блока связанного с фильтрами"""

    @pytest.mark.django_db
    def test_create_filter(self, api_client: APIClient,
                           create_box_filter: Callable[..., BoxFilter],
                           test_filter_data: dict[str, str]
                           ) -> None:
        """Тест создания фильтра."""

        box_filter = create_box_filter()

        filter_data = {
            'telegram_id': box_filter.box_id.user_id.telegram_id,
            'email_username': box_filter.box_id.email_username,
            'filter_data': {
                'filter_value': test_filter_data['filter_value'],
                'filter_name': test_filter_data['filter_name']
            }
        }

        response = api_client.post(f'{BASE_URL}/create', json.dumps(filter_data), content_type='application/json')

        assert response.status_code == 201
        assert response.json()['success'] == 'Filter created successfully'

        filter_exists = BoxFilter.objects.filter(
            box_id=box_filter.box_id,
            filter_value=filter_data['filter_data']['filter_value']
        ).exists()
        assert filter_exists

    @pytest.mark.django_db
    def test_get_filters_for_box_success(self, api_client: APIClient,
                                         create_email_box: Callable[..., EmailBox],
                                         create_box_filter: Callable[..., BoxFilter]
                                         ) -> None:
        """Тест получения фильтров для почтового ящика при корректных данных."""

        email_box = create_email_box()

        box_filter1 = create_box_filter(box_id=email_box)
        box_filter2 = create_box_filter(box_id=email_box)

        request_data = {
            'telegram_id': email_box.user_id.telegram_id,
            'email_username': email_box.email_username
        }

        response = api_client.post(BASE_URL, json.dumps(request_data), content_type='application/json')

        assert response.status_code == 200

        response_data = response.json()

        assert len(response_data) == 2
        assert any(filter_['filter_value'] == box_filter1.filter_value for filter_ in response_data)
        assert any(filter_['filter_value'] == box_filter2.filter_value for filter_ in response_data)

    @pytest.mark.django_db
    def test_get_filters_for_clean_box(self,
                                       api_client: APIClient,
                                       create_email_box: Callable[..., EmailBox]
                                       ) -> None:
        """Тест получения фильтров для почтового ящика при их отсутствии."""

        email_box = create_email_box()

        request_data = {
            'telegram_id': email_box.user_id.telegram_id,
            'email_username': email_box.email_username
        }

        response = api_client.post(BASE_URL, json.dumps(request_data), content_type='application/json')

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.django_db
    def test_get_filters_for_unexisted_email_box(self, api_client: APIClient,
                                                 create_bot_user: Callable[[int], BotUser],
                                                 test_user_data: dict[str, int]) -> None:
        """Тест получения фильтров для несуществующего почтового ящика"""

        user = create_bot_user(test_user_data['telegram_id'])

        request_data = {
            'telegram_id': user.telegram_id,
            'email_username': test_user_data['email_username']
        }
        response = api_client.post(BASE_URL, json.dumps(request_data), content_type='application/json')

        assert response.status_code == 404
        assert response.json()[
            'detail'] == (f'No email box found for user with telegram_id: {user.telegram_id} '
                          f'and email_username: {test_user_data["email_username"]}')
