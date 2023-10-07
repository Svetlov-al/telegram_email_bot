from typing import Any, Callable, Dict, TypedDict

import pytest
from api.tests.fixtures.email_fixtures import EmailBoxFactory
from email_service.models import BoxFilter, EmailBox
from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory


class BoxFilterFactory(DjangoModelFactory):
    class Meta:
        model = BoxFilter

    box_id = SubFactory(EmailBoxFactory)
    filter_value = Sequence(lambda n: f'filter_value_{n}')
    filter_name = Sequence(lambda n: f'filter_name_{n}')


@pytest.fixture
def create_box_filter(create_email_box) -> Callable:
    def make_box_filter(**kwargs):
        return BoxFilterFactory(**kwargs)

    return make_box_filter


@pytest.fixture
def test_filter_data() -> dict[str, str]:
    return {
        'filter_value': 'example@example.com',
        'filter_name': 'Yandex'
    }


class FilterData(TypedDict):
    """
    FilterData TypedDict.

    Описывает структуру данных для фильтра почтового ящика, которая включает в себя:
    - box_id: Ссылка на объект почтового ящика (EmailBox), к которому применяется фильтр.
    - filter_value: Значение фильтра, по которому происходит фильтрация сообщений.
    - filter_name: Название или идентификатор фильтра, используемый для его идентификации.

    Пример использования:
    filter_data = FilterData(
        box_id=email_box_instance,
        filter_value="important@example.com",
        filter_name="Вася пупкин"
    )
    """

    box_id: EmailBox
    filter_value: str
    filter_name: str
