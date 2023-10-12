from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from middleware import BackendConnector

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'


def format_box_info(data: dict) -> str:
    """Функция, которая принимает словарь с информацией о почтовом ящике и форматирует его в читабельный текст."""
    if not data:
        return 'Информация о почтовом ящике отсутствует.'

    message_text = '<b>Информация о вашем почтовом ящике:</b>\n\n'

    message_text += f"📧 <b>Email:</b> {data['email_username']}\n"
    message_text += f"🔊 <b>Отслеживание:</b> {'Да' if data['listening'] else 'Нет'}\n"
    message_text += f"🌐 <b>Почтовый сервис:</b> {data['email_service']['title']}\n"

    if not data['filters']:
        message_text += '<i>Фильтры отсутствуют</i>\n'
    else:
        message_text += '<b>Фильтры:</b>\n'
        for filter_ in data['filters']:
            message_text += f"• <i>{filter_['filter_name']}</i>: {filter_['filter_value']}\n"

    return message_text


async def get_available_services(backend_service: BackendConnector) -> list:
    """Получает список доступных сервисов с бэкенда."""
    response = await backend_service.get_data(endpoint='emailboxes/services')
    if response.status_code == 200:
        return response.json()
    return []


def create_service_keyboard(services: list) -> InlineKeyboardMarkup:
    """Создает клавиатуру с доступными сервисами."""
    keyboard = InlineKeyboardMarkup()

    if not services:
        keyboard.add(InlineKeyboardButton(text='🚫 Сервис не доступен', callback_data='unavailable_service'))
        keyboard.add(InlineKeyboardButton(text='🚫 Отмена', callback_data='return_in_menu'))
        return keyboard

    for service in services:
        button = InlineKeyboardButton(text=service['title'], callback_data=f"select_domain_{service['slug']}")
        keyboard.add(button)
    keyboard.add(InlineKeyboardButton(text='🚫 Отмена', callback_data='return_in_menu'))
    return keyboard


def create_email_boxes_keyboard(email_boxes: list) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру из списка почтовых ящиков.

    :param email_boxes: Список почтовых ящиков.
    :return: InlineKeyboardMarkup объект.
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    for box in email_boxes:
        button = InlineKeyboardButton(text=box['email_username'], callback_data=f"box_info:{box['email_username']}")
        keyboard.add(button)
    main_menu_button = InlineKeyboardButton(text='☰ В главное меню', callback_data='return_in_menu')
    keyboard.add(main_menu_button)
    return keyboard


def create_box_info_keyboard(box_info: dict) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру на основе информации о почтовом ящике.

    :param box_info: Словарь с информацией о почтовом ящике.
    :return: InlineKeyboardMarkup объект.
    """
    keyboard = InlineKeyboardMarkup(row_width=1)

    add_filter_button = InlineKeyboardButton(text='📥 Добавить фильтр', callback_data='add_filter')
    keyboard.add(add_filter_button)

    if box_info['listening']:
        stop_listening_button = InlineKeyboardButton(text='🔇 Остановить прослушивание', callback_data='stop_listening')
        keyboard.add(stop_listening_button)
    else:
        start_listening_button = InlineKeyboardButton(text='🔈 Начать прослушивание', callback_data='start_listening')
        keyboard.add(start_listening_button)

    back_button = InlineKeyboardButton(text='◀️ Назад', callback_data='go_back_to_boxes')
    keyboard.add(back_button)

    return keyboard
