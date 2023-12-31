import os

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from middleware import BackendServiceMiddleware, ThrottlingMiddleware

ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
TROTTLING_TIME = int(os.getenv('TROTTLING_TIME', 60))


bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher(bot=bot, storage=MemoryStorage())

dp.middleware.setup(BackendServiceMiddleware())
dp.middleware.setup(ThrottlingMiddleware())
