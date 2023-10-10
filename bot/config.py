import os

from aiogram import Bot, Dispatcher

bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher(bot)
