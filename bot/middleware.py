import asyncio
import os
from datetime import datetime, timedelta
from typing import Callable, Union

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware, LifetimeControllerMiddleware
from aiogram.utils.exceptions import MessageToDeleteNotFound, Throttled
from service import BackendConnector

BASE_URL = os.getenv('BASE_URL')
DEFAULT_RATE_LIMIT = 1


class BackendServiceMiddleware(LifetimeControllerMiddleware):
    skip_patterns = ['error', 'update']

    async def pre_process(self, obj, data, *args):
        backend_service = BackendConnector(BASE_URL)
        data['backend_service'] = backend_service


class ThrottlingMiddleware(BaseMiddleware):
    """Мидлвар для ограничения количества запросов."""

    def __init__(self, limit=DEFAULT_RATE_LIMIT, key_prefix='antiflood_'):
        self.rate_limit = limit
        self.prefix = key_prefix
        super().__init__()

    async def on_process_message(self, message: types.Message, data: dict) -> None:
        """Проверка ограничения при выполнении."""
        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()

        state_data: FSMContext = data.get('state')
        data = await state_data.get_data()
        limit = getattr(handler, 'throttling_rate_limit', self.rate_limit)
        key = getattr(
            handler,
            'throttling_key',
            f'{self.prefix}_{handler.__name__}_{message.chat.id}',
        ).format(**data)

        try:
            await dispatcher.throttle(key, rate=limit)
        except Throttled as t:
            await message.reply(
                f'Эту операцию нельзя выполнить чаще чем 1 раз в {t.rate:.0f}'
                f' секунд.\nС прошлого выполнения прошло {t.delta:.0f} секунд.'
                f'\nПопробуйте снова через {t.rate:.0f} секунд.'
            )
            raise CancelHandler()

    async def on_process_callback_query(self, callback_query: types.CallbackQuery, data: dict) -> None:
        """Проверка ограничения при выполнении колбэка."""
        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()

        state_data: FSMContext = data.get('state')
        data = await state_data.get_data()
        limit = getattr(handler, 'throttling_rate_limit', self.rate_limit)
        key = getattr(
            handler,
            'throttling_key',
            f'{self.prefix}_{handler.__name__}_{callback_query.from_user.id}',
        ).format(**data)

        try:
            await dispatcher.throttle(key, rate=limit)
        except Throttled as t:
            await callback_query.answer(
                f'Эту операцию нельзя выполнить чаще чем 1 раз в {t.rate:.0f}'
                f' секунд.\nС прошлого выполнения прошло {t.delta:.0f} секунд.'
                f'\nПопробуйте снова через {t.rate:.0f} секунд.',
                show_alert=True
            )
            raise CancelHandler()


def rate_limit(limit: int, key: str) -> Callable:
    """Декоратор для ограничения количества запросов."""
    def decorator(func):
        setattr(func, 'throttling_rate_limit', limit)
        setattr(func, 'throttling_key', key)
        return func
    return decorator
