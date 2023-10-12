from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

register_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='🖊 Регистрация', callback_data='register')
    ]
])

create_and_show_email_box_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='📥 Добавить почтовый ящик', callback_data='create_new_emailbox')
    ],
    [
        InlineKeyboardButton(text='📦 Мои почтовые ящики', callback_data='show_my_emailboxes')
    ],
    [
        InlineKeyboardButton(text='💡 Инструкция', callback_data='instruction')
    ]
])

continue_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='◀️ Назад', callback_data='return_in_menu'),
        InlineKeyboardButton(text='Продолжить ▶️', callback_data='continue_create_mail'),
    ]
])

main_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='◀️ Назад', callback_data='return_in_menu'),
    ]
])

general_main_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='☰ В главное меню', callback_data='return_in_menu'),
    ]
])

cancel_creating_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='🚫 Отмена', callback_data='return_in_menu'),
    ]
])

check_info_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='☑️ Подтвердить', callback_data='yes_create_email'),
        InlineKeyboardButton(text='↪️ В начало', callback_data='return_in_menu'),
    ]
])

check_filter_info_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='☑️ Подтвердить', callback_data='yes_add_new_filter'),
        InlineKeyboardButton(text='↪️ В начало', callback_data='return_in_menu'),
    ]
])
