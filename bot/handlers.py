from aiogram.types import Message, ParseMode
from config import bot, dp


@dp.message_handler(commands=['start'])
async def send_welcome(message: Message):
    await bot.send_message(chat_id=message.from_user.id,
                           text='Добро пожаловать в почтового бота "Почтальон печкин 📮"!',
                           parse_mode=ParseMode.HTML)
