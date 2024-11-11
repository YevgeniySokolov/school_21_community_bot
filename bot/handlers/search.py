import logging

from aiogram import F
from aiogram.dispatcher.router import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.decorators import db_session_decorator, private_only
from bot.keyboards.keyboards import (get_buttons, get_inline_keyboard,
                                     get_keyboard)
from bot.messages import Buttons, Messages
from bot.states.states import Search, Start_state
from bot.utils import (check_user_exists, get_user_admin, get_user_registered,
                       processing_user_list)
from database.models import Level, User
from settings import LIMIT, START_OFFSET

router = Router()
hndlr_logger = logging.getLogger('HNDLR_LOGGER')


# -----------------------SEARCHING BRANCH------------------------------
# Обработчик для кнопки "Продолжить"
@router.message(
    StateFilter(Start_state.wait_for_action),
    F.text == "Продолжить"
)
@private_only
@db_session_decorator
async def role_selection_keyb(message: Message, state: FSMContext, session):
    await state.update_data(offset=START_OFFSET)
    await state.update_data(limit=LIMIT)
    keyboard = await get_inline_keyboard(session, User)
    await message.answer(
        Messages.LETS_START,
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer(Messages.WHOS_LOOKING_FOR, reply_markup=keyboard)
    await state.set_state(Search.waiting_for_role)


# Фильтрация по роли
@router.callback_query(StateFilter(Search.waiting_for_role))
@private_only
@db_session_decorator
async def choosing_a_role(
    callback_query: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    await state.update_data(role=callback_query.data)
    keyboard = await get_inline_keyboard(session, Level)
    await callback_query.message.answer(
        Messages.WHAT_LEVEL,
        reply_markup=keyboard
    )
    await callback_query.answer()
    hndlr_logger.debug(str(callback_query.data))
    await state.set_state(Search.waiting_for_level)


# Обработка нажатия кнопки "Назад"
@router.callback_query(
    StateFilter(Search.waiting_for_level),
    F.data.lower().contains("back"),
)
@private_only
@db_session_decorator
async def go_to_searching_start(
    callback_query: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    keyboard = await get_inline_keyboard(session, User)
    await callback_query.message.answer(
        Messages.WHOS_LOOKING_FOR,
        reply_markup=keyboard
    )
    await callback_query.answer()
    await state.update_data(offset=START_OFFSET)
    await state.set_state(Search.waiting_for_role)


# Фильтрация по уровню и вывод списка
@router.callback_query(StateFilter(Search.waiting_for_level))
@private_only
@db_session_decorator
async def choosing_a_level(
    callback_query: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    get_level_id = await session.execute(
        select(Level.id).where(
            Level.name == callback_query.data
        )
    )
    level_id = int(get_level_id.scalar_one())
    list_counter: int = 0
    await state.update_data(
        level_id=level_id,
        list_counter=list_counter
    )
    await callback_query.answer()
    await processing_user_list(state, session, callback_query, list_counter)
    await state.set_state(Search.users_list)


# Обработка нажатия кнопки "Назад" при работе со списком
@router.callback_query(
    StateFilter(Search.users_list),
    F.data.lower().contains("back"),
)
@private_only
@db_session_decorator
async def get_next_users_list(
    callback_query: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    data = await state.get_data()
    list_counter = data['list_counter'] - 2
    offset = data['limit'] * list_counter
    await state.update_data(list_counter=list_counter)
    await state.update_data(offset=offset)
    await callback_query.answer()
    await processing_user_list(state, session, callback_query, list_counter)
    await state.set_state(Search.users_list)


# Обработка нажатия кнопки "Далее"
@router.callback_query(
    StateFilter(Search.users_list),
    F.data.contains("next")
)
@private_only
@db_session_decorator
async def get_next_users_lists(
    callback_query: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    data = await state.get_data()
    list_counter = data['list_counter']
    await callback_query.answer()
    await processing_user_list(state, session, callback_query, list_counter)
    await state.set_state(Search.users_list)


# Обработка нажатия кнопки "Просмотр" на одной из карточек
# Кнопки "В начало" и "Назад к списку"
@router.callback_query(
    StateFilter(Search.users_list),
    F.data.startswith("user_")
)
@private_only
@db_session_decorator
async def get_user_card(
    callback_query: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    user_id = callback_query.data.split('_')[1]
    data = await session.execute(
        select(
            User.sber_id,
            User.username,
            User.school21_nickname,
            User.role,
            Level.name,
            User.description
        ).join(
            Level,
            User.level_id == Level.id
        ).where(User.id == int(user_id))
    )
    result = data.first()
    user_card = Messages.CARD_MESSAGE.format(
        sber_id=result.sber_id,
        username=result.username,
        school21_nickname=result.school21_nickname,
        role=result.role,
        level=result.name,
        description=(
            result.description if result.description else 'Не указано'
        )
    )
    await callback_query.answer()
    keyboard = await get_buttons(
        to_begin=Buttons.TO_BEGIN,
        back=Buttons.TO_LIST
    )
    await state.update_data(offset=START_OFFSET)
    await state.update_data(list_counter=2)
    await callback_query.message.answer(user_card, reply_markup=keyboard)


# Возврат к началу диалога с ботом по кнопке "В начало"
@router.callback_query(
    F.data.contains("to_begin")
)
@db_session_decorator
@private_only
async def back_to_begin(
    callback_query: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    telegram_id = callback_query.from_user.id
    is_registered = await get_user_registered(session, telegram_id)
    existing_user = await check_user_exists(session, telegram_id)
    is_admin = await get_user_admin(session, telegram_id)
    keyboard = get_keyboard(
        is_registered=is_registered,
        existing_user=existing_user,
        is_admin=is_admin
    )
    await callback_query.answer()
    await state.set_state(Start_state.wait_for_action)
    await callback_query.message.answer(
        Messages.WELCOME_MESSAGE,
        reply_markup=keyboard
    )
