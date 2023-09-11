import os

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

API_TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply(
        "Hi!\nI'm EchoBot! Send me any text and I'll reply back."
    )


@dp.message_handler()
async def echo(message: types.Message):
    await message.reply(message.text)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
