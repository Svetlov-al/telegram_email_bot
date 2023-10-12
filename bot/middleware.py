import asyncio
import os

from aiogram import Dispatcher, types
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

    def __init__(self, limit=DEFAULT_RATE_LIMIT, key_prefix='antiflood_'):
        self.rate_limit = limit
        self.prefix = key_prefix
        super().__init__()

    async def throttle(self, target: types.Message | types.CallbackQuery):
        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()
        if not handler:
            return
        limit = getattr(handler, 'throttling_rate_limit', self.rate_limit)
        key = getattr(handler, 'throttling_key', f'{self.prefix}_{handler.__name__}')

        try:
            await dispatcher.throttle(key, rate=limit)
        except Throttled as t:
            await self.target_throttled(target, t, dispatcher, key)
            raise CancelHandler()

    @staticmethod
    async def target_throttled(target: types.Message | types.CallbackQuery,
                               throttled: Throttled, dispatcher: Dispatcher, key: str):
        msg = target.message if isinstance(target, types.CallbackQuery) else target
        delta = throttled.rate - throttled.delta

        info_msg = await msg.reply(f'Функция изменения статуса прослушивания доступна раз в 3 минуты.\n'
                                   f'⚠ Пожалуйста, подождите {round(delta, 1)} секунд перед следующим вызовом.')

        await asyncio.sleep(5)
        try:
            await msg.bot.delete_message(chat_id=msg.chat.id, message_id=info_msg.message_id)
        except MessageToDeleteNotFound:
            pass
        await asyncio.sleep(delta - 5)
        thr = await dispatcher.check_key(key)
        if thr.exceeded_count == throttled.exceeded_count:
            info_msg = await msg.reply('⚠ Все, теперь отвечаю.')
            try:
                await asyncio.sleep(5)
                await msg.bot.delete_message(chat_id=msg.chat.id, message_id=info_msg.message_id)
            except MessageToDeleteNotFound:
                pass

    async def on_process_message(self, message, data):  # noqa
        await self.throttle(message)

    async def on_process_callback_query(self, call, data):  # noqa
        await self.throttle(call)


def rate_limit(limit: int, key=None):
    def decorator(func):
        setattr(func, 'throttling_rate_limit', limit)
        if key:
            setattr(func, 'throttling_key', key)
        return func

    return decorator
