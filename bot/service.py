from aiogram.dispatcher.handler import CancelHandler
from bot_logger_config import logger
from httpx import AsyncClient, Response


class BackendConnector:
    """
    Сервис для асинхронного взаимодействия с удаленным backend API.

    Этот класс предоставляет методы для выполнения HTTP-запросов к заданному API.
    Он инкапсулирует логику подключения, формирования запросов и обработки ответов,
    предоставляя удобный интерфейс для взаимодействия с удаленными ресурсами.

    Attributes:
        api_url (str): Базовый URL API, с которым происходит взаимодействие.

    Methods:
        get_data(endpoint: str) -> Response:
            Выполняет GET-запрос к указанному endpoint и возвращает ответ.

        post_data(endpoint: str, data: dict) -> Response:
            Выполняет POST-запрос к указанному endpoint с переданными данными и возвращает ответ.
    """

    def __init__(self, api_url: str):
        self.api_url = api_url

    async def get_data(self, endpoint: str) -> Response:
        """Выполняет GET-запрос к указанному endpoint."""
        url = f'{self.api_url}/{endpoint}'
        try:
            async with AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
            return response
        except Exception as e:
            logger.error(f'Error during GET request to {url}: {e}')
            raise CancelHandler()

    async def post_data(self, endpoint: str, data: dict[str, str | int | bool | list[dict[str, str]]]) -> Response:
        """Выполняет POST-запрос к указанному endpoint с переданными данными."""
        url = f'{self.api_url}/{endpoint}'
        try:
            async with AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=data)
            return response
        except Exception as e:
            logger.error(f'Error during POST request to {url} with data {data}: {e}')
            # В зависимости от вашего кода, вы можете вернуть None или какой-либо другой объект
            raise CancelHandler()
