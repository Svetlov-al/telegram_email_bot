import asyncio
import re

import aiogram.utils.exceptions
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message, ParseMode
from aiogram.utils.exceptions import MessageToDeleteNotFound
from bot_logger_config import logger
from config import ENCRYPTION_KEY, bot, dp
from crypto.crypto_utils import PasswordCipher
from keyboards import (
    cancel_creating_kb,
    check_filter_info_kb,
    check_info_kb,
    continue_kb,
    create_and_show_email_box_kb,
    general_main_menu_kb,
    main_menu_kb,
    register_kb,
)
from messages import INSTRUCTION_MESSAGE
from middleware import rate_limit
from photo_urls import (
    CHECK_INFO_PHOTO,
    ENTER_EMAIL_DATA_PHOTO,
    FAIL_LISTENING,
    INSTRUCTION_PHOTO,
    MAIL_PHOTO,
    MAIL_REGISTRATION_PHOTO,
    MY_BOXES_PHOTO,
    SUCCES_LISTENING,
)
from service import BackendConnector
from states.user_states import BotStates, RegistrationBox
from utils import (
    EMAIL_REGEX,
    create_box_info_keyboard,
    create_email_boxes_keyboard,
    create_service_keyboard,
    format_box_info,
    get_available_services,
)


@dp.message_handler(commands=['start'], state='*')
async def send_welcome(message: Message, backend_service: BackendConnector):
    """Приветственная комманда. Начало работы с ботом."""
    telegram_id = message.from_user.id

    response = await backend_service.get_data(f'users/{telegram_id}')

    if response.status_code == 200:
        await bot.send_photo(chat_id=telegram_id,
                             photo=MAIL_PHOTO,
                             caption='Добро пожаловать обратно в почтового бота <b>"Почтальон Печкин</b> 📮"!',
                             reply_markup=create_and_show_email_box_kb,
                             parse_mode=ParseMode.HTML)
        await BotStates.MainMenuState.set()
    else:
        message_text = ("Добро пожаловать в почтового бота <b>\"Почтальон Печкин\" 📮</b>!\n\n"
                        'Здесь вы можете зарегистрировать свой почтовый ящик и настроить фильтры для него. '
                        'После регистрации, вы будете получать письма от вашего ящика прямо здесь, в виде картинки. '
                        'Таким образом, вы сможете быстро оценить важность каждого сообщения и решить, стоит ли его открывать.\n\n'
                        '<i>Для начала работы, пожалуйста, зарегистрируйтесь.</i>')
        await bot.send_photo(chat_id=telegram_id,
                             photo=MAIL_PHOTO,
                             caption=message_text,
                             reply_markup=register_kb,
                             parse_mode=ParseMode.HTML)
        await BotStates.UserCreateState.set()


@dp.callback_query_handler(lambda c: c.data == 'return_in_menu', state='*')
async def main_menu_callback_command(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки возврат в главное меню"""

    media = InputMediaPhoto(media=MAIL_REGISTRATION_PHOTO,
                            caption='Добро пожаловать обратно в почтового бота <b>"Почтальон Печкин</b> 📮"!',
                            parse_mode=ParseMode.HTML)
    await callback.message.edit_media(media=media, reply_markup=create_and_show_email_box_kb)
    await state.reset_state()
    await BotStates.MainMenuState.set()


@dp.callback_query_handler(lambda c: c.data == 'instruction', state=BotStates.MainMenuState)
async def instruction_handler(callback: CallbackQuery):
    """Обработчик кнопки иснтрукция."""
    media = InputMediaPhoto(media=INSTRUCTION_PHOTO, caption=INSTRUCTION_MESSAGE, parse_mode=ParseMode.HTML)
    await callback.message.edit_media(media=media, reply_markup=main_menu_kb)


@dp.callback_query_handler(lambda c: c.data == 'hide_notification_message', state='*')
async def hide_message_handler(callback: CallbackQuery):
    try:
        await bot.delete_message(chat_id=callback.from_user.id, message_id=callback.message.message_id)
    except MessageToDeleteNotFound:
        pass


@dp.callback_query_handler(lambda c: c.data == 'register', state=BotStates.UserCreateState)
async def register_user(callback: CallbackQuery, backend_service: BackendConnector):
    """Обработчик кнопки Регистрация."""
    telegram_id = callback.from_user.id
    data = {
        'telegram_id': telegram_id,
    }
    response = await backend_service.post_data('users', data=data)
    if response.status_code == 201:
        message_text = ('🎉 <b>Поздравляем!</b> 🎉\n\nВы успешно зарегистрировались в нашем боте.\n'
                        'Теперь вы можете создать почтовые ящики для отслеживания и начать получать уведомления прямо здесь.\n'
                        'Начните с добавления вашего первого почтового ящика и настройте его по вашему усмотрению.\n'
                        'Будем рады помочь вам оставаться в курсе всех ваших писем!')
        await callback.message.edit_caption(caption=message_text,
                                            parse_mode=ParseMode.HTML,
                                            reply_markup=create_and_show_email_box_kb)
        await BotStates.MainMenuState.set()
    else:
        message_text = ('😔 К сожалению произошла непредвиденная ошибка!\n'
                        'Возможно сервис сейчас не доступен\n'
                        'Попробуйте осуществить регистрацию немного позже!')
        await callback.message.edit_caption(caption=message_text,
                                            parse_mode=ParseMode.HTML,
                                            reply_markup=register_kb)
        await BotStates.UserCreateState.set()


@dp.callback_query_handler(lambda c: c.data == 'create_new_emailbox', state=BotStates.MainMenuState)
async def create_new_email_box(callback: CallbackQuery):
    """Обработчик кнопки для создания почтового ящика."""
    message_text = ('Для регистрации почтового ящика, пожалуйста, подготовьте следующую информацию:\n\n'
                    '1. Почтовый ящик в формате: <b>username@example.com</b>\n'
                    '2. Пароль от вашего почтового ящика.\n'
                    '3. Фильтры для писем:\n'
                    '   - Название фильтра\n'
                    '   - Значение фильтра\n\n'
                    'Эти данные необходимы для того, чтобы вы могли получать письма из указанного ящика прямо в этом телеграм-боте.')
    media = InputMediaPhoto(media=MAIL_REGISTRATION_PHOTO,
                            caption=message_text,
                            parse_mode=ParseMode.HTML)
    await callback.message.edit_media(media=media, reply_markup=continue_kb)
    await BotStates.EmailBoxCreateState.set()


@dp.callback_query_handler(lambda c: c.data == 'continue_create_mail', state=BotStates.EmailBoxCreateState)
async def continue_create_mail_handler(callback: CallbackQuery, backend_service: BackendConnector):
    services = await get_available_services(backend_service)
    keyboard = create_service_keyboard(services)

    message_text = '<b>Выберите пожалуйста Ваш почтовый сервис ⤵️: </b>'
    media = InputMediaPhoto(media=ENTER_EMAIL_DATA_PHOTO, caption=message_text, parse_mode=ParseMode.HTML)
    await callback.message.edit_media(media=media, reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('select_domain_'), state=BotStates.EmailBoxCreateState)
async def select_email_domain_handler(callback: CallbackQuery, state: FSMContext, backend_service: BackendConnector):
    selected_slug = callback.data.replace('select_domain_', '')

    services = await get_available_services(backend_service)
    selected_service = next((service for service in services if service['slug'] == selected_slug), None)

    if selected_service:
        await state.update_data(slug=selected_service['slug'], slug_title=selected_service['title'])
        parent_message = await callback.message.edit_caption(
            caption='Пожалуйста, введите ваше <b>имя пользователя (логин)</b> для выбранного почтового сервиса ⤵️:',
            parse_mode=ParseMode.HTML,
            reply_markup=cancel_creating_kb)
        await state.update_data(parent_message=parent_message.message_id)
        await RegistrationBox.WaitForUserNameState.set()


@dp.message_handler(state=RegistrationBox.WaitForUserNameState)
async def process_username(message: Message, state: FSMContext):
    if re.match(EMAIL_REGEX, message.text):

        username = message.text.strip()
        await state.update_data(username=username)
        message_id = (await state.get_data()).get('parent_message')

        await bot.edit_message_caption(
            chat_id=message.from_user.id,
            message_id=message_id,
            caption=f'Имя пользователя: {username}\n'
                    f'Пожалуйста, введите ваш <b>пароль</b> для почтового ящика ⤵️:',
            parse_mode=ParseMode.HTML,
            reply_markup=cancel_creating_kb)
        await message.delete()
        await RegistrationBox.WaitForPasswordState.set()
    else:
        fail_message = await message.answer(
            'Введен некорректный формат email. Пожалуйста, введите email в формате username@example.com.')
        await asyncio.sleep(5)
        await message.delete()
        await bot.delete_message(chat_id=message.chat.id, message_id=fail_message.message_id)


@dp.message_handler(state=RegistrationBox.WaitForPasswordState)
async def process_password(message: Message, state: FSMContext):
    password = message.text.strip()

    await state.update_data(password=password)
    message_id = (await state.get_data()).get('parent_message')
    username = (await state.get_data()).get('username')
    await bot.edit_message_caption(
        chat_id=message.from_user.id,
        message_id=message_id,
        caption=f'Имя пользователя: {username}\n'
                f'Пароль: {password}\n\n'
                'Для того чтобы создать хотябы один <b>фильтр</b>,\n<b>введите его название</b> ⤵️:',
        parse_mode=ParseMode.HTML,
        reply_markup=cancel_creating_kb)
    await message.delete()
    await RegistrationBox.WaitForFilterNameState.set()


@dp.message_handler(state=RegistrationBox.WaitForFilterNameState)
async def process_filter_name(message: Message, state: FSMContext):
    filter_name = message.text.strip()

    await state.update_data(filter_name=filter_name)
    message_id = (await state.get_data()).get('parent_message')
    username = (await state.get_data()).get('username')
    password = (await state.get_data()).get('password')

    await bot.edit_message_caption(
        chat_id=message.from_user.id,
        message_id=message_id,
        caption=f'Имя пользователя: {username}\n'
                f'Пароль: {password}\n'
                f'Название фильтра: {filter_name}\n\n'
                'Пожалуйста, введите <b>email для фильтра</b>, письма от которого вы хотите получать, \nв формате username@example.com. ⤵️:',
        parse_mode=ParseMode.HTML,
        reply_markup=cancel_creating_kb)
    await message.delete()
    await RegistrationBox.WaitForFilterValueState.set()


@dp.message_handler(state=RegistrationBox.WaitForFilterValueState)
async def process_filter_value(message: Message, state: FSMContext):
    if re.match(EMAIL_REGEX, message.text):
        filter_value = message.text.strip()
        await state.update_data(filter_value=filter_value)
        user_data = await state.get_data()

        info_text = f"""
        <b>Пожалуйста, проверьте введенные вами данные:</b>

🌐 Почтовый сервис: {user_data['slug_title']}
📧 Имя пользователя: {user_data['username']}
🔒 Пароль: {'*' * len(user_data['password'])} (скрыт)
🔍 Название фильтра: {user_data['filter_name']}
📩 Email для фильтра: {user_data['filter_value']}
"""

        message_id = (await state.get_data()).get('parent_message')

        media = InputMediaPhoto(media=CHECK_INFO_PHOTO, caption=info_text, parse_mode=ParseMode.HTML)
        await bot.edit_message_media(chat_id=message.from_user.id,
                                     message_id=message_id,
                                     media=media,
                                     reply_markup=check_info_kb)
        await message.delete()
        await RegistrationBox.CheckEmailInfoState.set()
    else:
        fail_message = await message.answer(
            'Введен некорректный формат email. Пожалуйста, введите email в формате username@example.com.')
        await asyncio.sleep(5)
        await message.delete()
        await bot.delete_message(chat_id=message.chat.id, message_id=fail_message.message_id)


@dp.callback_query_handler(lambda c: c.data == 'yes_create_email', state=RegistrationBox.CheckEmailInfoState)
async def confirm_email_create_handler(callback: CallbackQuery, state: FSMContext, backend_service: BackendConnector):
    user_data = await state.get_data()

    cipher = PasswordCipher(ENCRYPTION_KEY)

    encrypted_password = cipher.encrypt_password(user_data['password'])

    data = {
        'user_id': callback.from_user.id,
        'email_service_slug': user_data['slug'],
        'email_username': user_data['username'],
        'email_password': encrypted_password.decode(),
        'filters': [
            {
                'filter_value': user_data['filter_value'],
                'filter_name': user_data['filter_name']
            }
        ]
    }

    response = await backend_service.post_data('emailboxes', data=data)
    if response.status_code == 201:
        message_text = (
            '<b>🎉 Прослушивание почты успешно запущено! 🎉</b>\n\n'
            'Теперь, при поступлении письма от указанного отправителя, бот будет автоматически отправлять вам изображение с содержимым письма.\n'
            'Оставайтесь на связи и не пропустите ни одного важного уведомления!'
        )
        media = InputMediaPhoto(media=SUCCES_LISTENING,
                                caption=message_text,
                                parse_mode=ParseMode.HTML)
        await callback.message.edit_media(media=media, reply_markup=general_main_menu_kb)
    elif response.status_code == 400:
        error_detail = response.json().get('detail', 'Неизвестная ошибка')
        media = InputMediaPhoto(media=FAIL_LISTENING, caption=f'❌ Ошибка: {error_detail}',
                                parse_mode=ParseMode.HTML)
        await callback.message.edit_media(media=media, reply_markup=main_menu_kb)


@dp.callback_query_handler(lambda c: c.data == 'show_my_emailboxes', state=BotStates.MainMenuState)
async def show_my_emailboxes(callback: CallbackQuery, backend_service: BackendConnector):
    telegram_id = callback.from_user.id
    response = await backend_service.get_data(f'users/{telegram_id}/boxes')
    email_boxes = response.json()
    keyboard = create_email_boxes_keyboard(email_boxes)
    await callback.message.edit_caption('Выберите почтовый ящик:',
                                        reply_markup=keyboard,
                                        parse_mode=ParseMode.HTML)
    await BotStates.ShowCaseState.set()


@dp.callback_query_handler(lambda c: c.data.startswith('box_info:'), state=BotStates.ShowCaseState)
async def show_box_info(callback: CallbackQuery,
                        backend_service: BackendConnector,
                        state: FSMContext,
                        from_listening=False):
    """Обработчик, который показывает подробную информацию о конкртеном почтовом ящике."""
    if from_listening:
        box_info = (await state.get_data()).get('box_info')
        email_username = box_info.get('email_username')
    else:
        email_username = callback.data.split(':')[1]
    data = {
        'telegram_id': callback.from_user.id,
        'email_username': email_username,
    }
    response = await backend_service.post_data('emailboxes/info', data=data)

    if response.status_code == 200:
        box_info = response.json()
        message_text = format_box_info(box_info)
        keyboard = create_box_info_keyboard(box_info)
        await state.update_data(box_info=box_info)
    else:
        error_detail = response.json().get('detail', [])
        if error_detail and isinstance(error_detail, list):
            message_text = error_detail[0].get('msg', 'Произошла неизвестная ошибка.')
        else:
            message_text = error_detail
        keyboard = main_menu_kb
    media = InputMediaPhoto(media=MY_BOXES_PHOTO, caption=message_text, parse_mode=ParseMode.HTML)
    try:
        await callback.message.edit_media(media=media, reply_markup=keyboard)
    except aiogram.utils.exceptions.MessageNotModified:
        pass


@dp.callback_query_handler(lambda c: c.data == 'go_back_to_boxes', state=BotStates.ShowCaseState)
async def go_back_to_boxes(callback: CallbackQuery, backend_service: BackendConnector, state: FSMContext):
    """Обработчик кнопки назад из информации о почтовом ящике к списку почтовых ящиков."""
    await state.reset_state()
    await show_my_emailboxes(callback, backend_service)


@dp.callback_query_handler(lambda c: c.data == 'add_filter', state=BotStates.ShowCaseState)
async def add_new_filter(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки добавления нового фильтра для почтового ящика."""
    parent_message = await callback.message.edit_caption(
        caption='Для того чтобы создать фильтр, введите его название ⤵️:',
        parse_mode=ParseMode.HTML,
        reply_markup=cancel_creating_kb)
    await state.update_data(parent_message=parent_message.message_id)
    await RegistrationBox.WaitForNewFilterNameState.set()


@dp.message_handler(state=RegistrationBox.WaitForNewFilterNameState)
async def process_new_filter_name(message: Message, state: FSMContext):
    filter_name = message.text.strip()
    message_id = (await state.get_data()).get('parent_message')
    await state.update_data(filter_name=filter_name)
    await bot.edit_message_caption(
        chat_id=message.from_user.id,
        message_id=message_id,
        caption=f'Название фильтра: {filter_name}\n\n'
                'Пожалуйста, введите email для фильтра, письма от которого вы хотите получать, \nв формате username@example.com. ⤵️:',
        reply_markup=cancel_creating_kb)
    await message.delete()
    await RegistrationBox.WaitForNewFilterValueState.set()


@dp.message_handler(state=RegistrationBox.WaitForNewFilterValueState)
async def process_new_filter_value(message: Message, state: FSMContext):
    if re.match(EMAIL_REGEX, message.text):
        filter_value = message.text.strip()
        await state.update_data(filter_value=filter_value)
        user_data = await state.get_data()

        info_text = f"""
            <b>Пожалуйста, проверьте введенные вами данные:</b>
🔍 Название фильтра: {user_data['filter_name']}
📩 Email для фильтра: {user_data['filter_value']}
    """

        message_id = (await state.get_data()).get('parent_message')

        media = InputMediaPhoto(media=CHECK_INFO_PHOTO, caption=info_text, parse_mode=ParseMode.HTML)
        await bot.edit_message_media(chat_id=message.from_user.id,
                                     message_id=message_id,
                                     media=media,
                                     reply_markup=check_filter_info_kb)
        await message.delete()
        await RegistrationBox.CheckFilterInfoState.set()
    else:
        fail_message = await message.answer(
            'Введен некорректный формат email. Пожалуйста, введите email в формате username@example.com.')
        await asyncio.sleep(5)
        await message.delete()
        await bot.delete_message(chat_id=message.chat.id, message_id=fail_message.message_id)


@dp.callback_query_handler(lambda c: c.data == 'yes_add_new_filter', state=RegistrationBox.CheckFilterInfoState)
async def yes_add_new_filter_handler(callback: CallbackQuery, backend_service: BackendConnector, state: FSMContext):
    user_data = await state.get_data()
    box_info = user_data.get('box_info')
    data = {
        'telegram_id': callback.from_user.id,
        'email_username': box_info['email_username'],
        'filter_data': {
            'filter_value': user_data['filter_value'],
            'filter_name': user_data['filter_name']
        }
    }

    response = await backend_service.post_data('filters/create', data=data)
    if response.status_code == 201:
        message_text = (
            '<b>🎉 Новый фильтр успешно добавлен! 🎉</b>\n\n'
            'Теперь, при поступлении письма, соответствующего вашему фильтру, бот будет автоматически отправлять вам уведомление.\n'
            'Оставайтесь на связи и не пропустите ни одного важного письма, соответствующего вашим критериям!'
        )
        media = InputMediaPhoto(media=SUCCES_LISTENING,
                                caption=message_text,
                                parse_mode=ParseMode.HTML)
        await callback.message.edit_media(media=media, reply_markup=general_main_menu_kb)
    elif response.status_code == 400:
        error_detail = response.json().get('detail', 'Неизвестная ошибка')
        media = InputMediaPhoto(media=FAIL_LISTENING, caption=f'❌ Ошибка: {error_detail}',
                                parse_mode=ParseMode.HTML)
        await callback.message.edit_media(media=media, reply_markup=main_menu_kb)


@rate_limit(limit=180, key='listening')
@dp.callback_query_handler(lambda c: c.data == 'start_listening', state=BotStates.ShowCaseState)
async def start_listening_handler(callback: CallbackQuery, backend_service: BackendConnector, state: FSMContext):
    box_info = (await state.get_data()).get('box_info')
    data = {
        'telegram_id': callback.from_user.id,
        'email_username': box_info.get('email_username'),
    }
    response = await backend_service.post_data('emailboxes/start_listening', data=data)
    if response.status_code == 200:
        await show_box_info(callback, backend_service, state, from_listening=True)
    else:
        error_message = response.json().get('detail', 'Error')
        await callback.message.edit_caption(caption=error_message,
                                            parse_mode=ParseMode.HTML,
                                            reply_markup=general_main_menu_kb)
        logger.error(error_message)


@rate_limit(limit=180, key='listening')
@dp.callback_query_handler(lambda c: c.data == 'stop_listening', state=BotStates.ShowCaseState)
async def stop_listening_handler(callback: CallbackQuery, backend_service: BackendConnector,
                                 state: FSMContext):
    box_info = (await state.get_data()).get('box_info')
    data = {
        'telegram_id': callback.from_user.id,
        'email_username': box_info.get('email_username'),
    }
    response = await backend_service.post_data('emailboxes/stop_listening', data=data)
    if response.status_code == 200:
        await show_box_info(callback, backend_service, state, from_listening=True)
    else:
        error_message = response.json().get('detail', 'Error')
        await callback.message.edit_caption(caption=error_message,
                                            parse_mode=ParseMode.HTML,
                                            reply_markup=general_main_menu_kb)
        logger.error(error_message)
