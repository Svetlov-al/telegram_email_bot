from typing import Callable

import pytest
from api.tests.fixtures.email_fixtures import EmailBoxData
from email_service.models import EmailBox, EmailService
from rest_framework.test import APIClient

BASE_URL = '/api/v1/emailboxes'


class TestEmails:
    """Класс для тестирования блока связанного с почтовыми ящиками"""

    @pytest.mark.django_db
    def test_all_domains(self,
                         api_client: APIClient
                         ) -> None:
        """Тест получения пустого списка доступных доменов."""

        response = api_client.get(f'{BASE_URL}/services')

        assert response.json() == []

    @pytest.mark.django_db
    def test_not_empty_all_domains(self,
                                   api_client: APIClient,
                                   create_email_service: Callable[[], EmailService]
                                   ) -> None:
        """Тест получения списка доступных доментов"""

        domain = create_email_service()

        response = api_client.get(f'{BASE_URL}/services')
        response_data = response.json()

        assert response.status_code == 200
        assert len(response_data) == 1
        assert response_data[0]['title'] == domain.title

    @pytest.mark.django_db
    def test_create_email_box(self,
                              api_client: APIClient,
                              create_email_box: Callable[[], EmailBox],
                              test_email_data: EmailBoxData
                              ) -> None:
        """Тест создания почтового ящика"""

        # email_box = create_email_box()
