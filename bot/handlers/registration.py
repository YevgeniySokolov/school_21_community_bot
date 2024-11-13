import asyncio
import logging
# import re

from aiogram import F
from aiogram.dispatcher.router import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from bot.decorators import db_session_decorator, private_only
from bot.handlers.search import role_selection_keyb
from bot.keyboards.keyboards import (get_confirm_keyboard,
                                     get_join_community_keyboard, get_keyboard,
                                     get_skip_inline_keyboard)
from bot.messages import Messages
from bot.states.states import Registration, Start_state
from bot.utils import (check_user_exists, get_user_admin, get_user_db_data,
                       get_user_registered, parse_level_and_role,
                       save_or_update_user, send_invite_link, timer_action)
from bot.validators.base import validate_and_update_state
from bot.validators.validators import (validate_description, validate_sber_id,
                                       validate_school21_nickname,
                                       validate_team_name)
from logger.logmessages import LogMessage
from settings import STATES_COLLECTION

router = Router()
hndlr_logger = logging.getLogger('HNDLR_LOGGER')

# Кортеж для возобновления аутентификации
CONTINUE_REG_TUPLE = (
    (Messages.ENTER_NICK_SCHOOL_MESSAGE,
     Registration.waiting_for_school21_nickname),
    (Messages.ENTER_SBER_ID_MESSAGE,
     Registration.waiting_for_sber_id),
    (Messages.ENTER_TEAM_MESSAGE,
     Registration.waiting_for_team_name),
    (Messages.ENTER_ROLE_IN_TEAM,
     Registration.waiting_for_role_level),
    (Messages.ENTER_ABOUT,
     Registration.waiting_for_activity_description)
)


# Обработчик команды /start

@router.message(Command("start"))
@db_session_decorator
@private_only
async def send_welcome(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    await state.set_state(Start_state.wait_for_action)
    telegram_id = message.from_user.id
    is_registered = await get_user_registered(session, telegram_id)
    is_admin = await get_user_admin(session, telegram_id)
    existing_user = await check_user_exists(session, telegram_id)
    keyboard = get_keyboard(is_registered, existing_user, is_admin)
    await message.answer(Messages.WELCOME_MESSAGE,
                         reply_markup=keyboard)
    hndlr_logger.info(
        LogMessage.USER_LINK.format(message.from_user.id)
    )
    if not is_registered and existing_user:
        hndlr_logger.info(
            LogMessage.GO_TO_CONTINUE_REG
        )
        await message.answer(Messages.CONTINUE_REG_MESSAGE)
        await message.answer(Messages.AUTH_MESSAGE, reply_markup=keyboard)
    elif not is_registered:
        hndlr_logger.info(
            LogMessage.GO_TO_REG
        )
        await message.answer(Messages.NOT_REGISTERED_MESSAGE)
        await message.answer(Messages.AUTH_MESSAGE, reply_markup=keyboard)


# -----------------------REGISTRATION BRANCH------------------------------
@router.message(F.text.in_(["Пройти аутентификацию",
                            "Пройти аутентификацию заново"]))
@private_only
@db_session_decorator
async def reg_action(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    # Включение таймера прерывания регистрации
    timer_task = asyncio.create_task(timer_action(message, state, session))
    await state.update_data(timer_task=timer_task)
    # Запросить пользователя ввести ник в Школе 21
    await message.answer(
        Messages.ENTER_NICK_SCHOOL_MESSAGE,
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Registration.waiting_for_school21_nickname)


@router.message(F.text == "Возобновить аутентификацию")
@private_only
@db_session_decorator
async def continue_reg_action(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    timer_task = asyncio.create_task(timer_action(message, state, session))
    await state.update_data(timer_task=timer_task)
    # Получаем данные из БД по заполненным полям
    user_fields = await get_user_db_data(session, message.from_user.id)
    # Заполняем state данными
    reg_step = len(user_fields) - 1
    for i in range(reg_step):
        await state.update_data({STATES_COLLECTION[i]: user_fields[i]})
    # Переходим к нужному шагу
    if reg_step == 5:
        keyboard = await get_confirm_keyboard()
        await message.answer(
            Messages.CONFIRM_MESSAGE, reply_markup=keyboard
        )
    else:
        if reg_step == 4:
            await message.answer(
                Messages.ENTER_ABOUT,
                reply_markup=get_skip_inline_keyboard()
            )
        else:
            await message.answer(CONTINUE_REG_TUPLE[reg_step][0])
        await state.set_state(CONTINUE_REG_TUPLE[reg_step][1])


@router.message(Registration.waiting_for_school21_nickname)
@private_only
@db_session_decorator
async def process_school21_nickname(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    # Валидация никнейма
    if await validate_and_update_state(
        message,
        state,
        validate_school21_nickname,
        'school21_nickname',
        session
    ):
        # Запросить пользователя SberID
        await message.answer(Messages.ENTER_SBER_ID_MESSAGE)
        await state.set_state(Registration.waiting_for_sber_id)


# Запросить SberID и ожидание ввода пользователя SberID
@router.message(Registration.waiting_for_sber_id)
@private_only
@db_session_decorator
async def process_sber_id(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    # Валидация sber_id
    if await validate_and_update_state(
        message,
        state,
        validate_sber_id,
        'sber_id',
        session
    ):
        # Запросить название команды
        await message.answer(Messages.ENTER_TEAM_MESSAGE)
        await state.set_state(Registration.waiting_for_team_name)


@router.message(Registration.waiting_for_team_name)
@private_only
@db_session_decorator
async def process_team_number(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    # Валидация названия команды
    if await validate_and_update_state(
        message,
        state,
        validate_team_name,
        'team_name',
        session
    ):
        # Запросить номер роли
        await message.answer(Messages.ENTER_ROLE_IN_TEAM)
        await state.set_state(Registration.waiting_for_role_level)


@router.message(Registration.waiting_for_role_level)
@private_only
@db_session_decorator
async def process_role(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    # role_level_pattern = r"^(Junior|Middle|Senior|Lead|Стажер)\s([а-яА-Яa-zA-Z][а-яА-Яa-zA-Z\- ]*)$"
    # match = re.match(role_level_pattern, message.text)
    # if match is None or not match.group(2):
    #     await message.answer(
    #         "Введите, пожалуйста, корректный уровень и роль через пробел\n"
    #         "Например, Senior python разработчик"
    #     )
    #     return

    # Получаем ответ об уровне и роли пользователя
    await state.update_data(role_level=message.text)

    # Над чем работаешь? И кнопка пропустить
    await message.answer(
        Messages.ENTER_ABOUT,
        reply_markup=get_skip_inline_keyboard()
    )
    await state.set_state(Registration.waiting_for_activity_description)


@router.callback_query(F.data == "skip_description")
@private_only
@db_session_decorator
async def skip_description_callback(
    callback_query,
    state: FSMContext,
    session: AsyncSession,
):
    await state.set_state(Registration.waiting_for_skip_description)
    await state.update_data(activity_description='Шаг пропущен')
    # Передаем флаг skip=True для обработки пропуска
    await process_activity_description(
        callback_query.message, state, skip=True
    )
    await callback_query.answer()  # Закрываем уведомление


@router.message(Registration.waiting_for_activity_description)
@private_only
@db_session_decorator
async def process_activity_description(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    skip=False,
):
    if skip:
        keyboard = await get_confirm_keyboard()
        await message.answer(
            Messages.CONFIRM_MESSAGE, reply_markup=keyboard
        )
        await state.set_state(Registration.waiting_for_final_confirmation)
        return

    # Валидация названия команды
    if not await validate_and_update_state(
        message,
        state,
        validate_description,
        'description',
        session
    ):
        return
    # Теперь можно сохранить все данные в базе данных
    hndlr_logger.info(
        LogMessage.ALL_DATA_RECEIVED.format(message.from_user.id)
    )
    # Сохранить описание деятельности
    await state.update_data(
        activity_description=message.text
    )
    keyboard = await get_confirm_keyboard()
    await message.answer(
        Messages.CONFIRM_MESSAGE, reply_markup=keyboard
    )


# Обработчик нажатия на кнопку "Присоединиться к комьюнити"
@router.callback_query(F.data == "confirm")
@private_only
@db_session_decorator
async def handle_join_community(
    callback_query: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    data = await state.get_data()
    if 'timer_task' in data:
        timer_task = data['timer_task']
        if not timer_task.done():  # Проверяем, завершена ли задача
            # Отменяем таймер
            timer_task.cancel()
    # Устанавливаем флаг, что регистрация на финальной стадии
    await state.set_state(Registration.waiting_for_final_confirmation)
    telegram_id = callback_query.from_user.id
    telegram_name = callback_query.from_user.username
    user_data = await state.get_data()
    level_id, role = await parse_level_and_role(
        user_data['role_level'], session
    )
    await save_or_update_user(session, telegram_id,
                              telegram_name, user_data,
                              role, level_id)
    await state.clear()
    hndlr_logger.info(
        LogMessage.USER_SAVED_TO_DB.format(
            callback_query.message.from_user.id
        )
    )
    # Ссылка на сообщество для пользователя
    invite_link = await send_invite_link(
        callback_query.bot,
        callback_query.message
    )
    if invite_link:
        keyboard = await get_join_community_keyboard(invite_link)
    await callback_query.message.answer(
        Messages.FINISH_REGISTRATION_MESSAGE, reply_markup=keyboard
    )
    await callback_query.answer()


@router.callback_query(F.data == "search_peers")
@private_only
@db_session_decorator
async def handle_search_peers(
    callback_query: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
):
    message = callback_query.message
    await role_selection_keyb(message, state)
    await callback_query.answer()  # Закрываем уведомление
