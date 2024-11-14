from unittest.mock import AsyncMock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, KeyboardButton,
                           ReplyKeyboardMarkup, ReplyKeyboardRemove)
from sqlalchemy.ext.asyncio import AsyncSession

from .test_registration import (create_mock_chat, create_mock_message,
                                create_mock_user)
from bot.handlers.search import (back_to_begin, choosing_a_role,
                                 go_to_searching_start, role_selection_keyb)
from bot.messages import Messages
from bot.states.states import Search
from settings import LIMIT, START_OFFSET


@pytest.fixture
def mock_objects():
    """Создает и возвращает мок-объекты для тестов."""
    mock_user = create_mock_user()
    mock_chat = create_mock_chat()
    mock_message = create_mock_message(mock_user, mock_chat)
    mock_callback_query = AsyncMock(spec=CallbackQuery)
    mock_callback_query.message = mock_message
    return mock_user, mock_chat, mock_message, mock_callback_query


@pytest.mark.asyncio
async def test_role_selection_keyb(mock_objects):
    """Тестирование кнопки "Продолжить"."""
    mock_user, mock_chat, mock_message, mock_callback_query = mock_objects
    mock_state = AsyncMock(spec=FSMContext)
    mock_session = AsyncMock(spec=AsyncSession)

    mock_state.update_data = AsyncMock()
    mock_state.set_state = AsyncMock()

    mock_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="golang разработчик",
            callback_data="golang разработчик"
        )]
    ])

    with patch(
        "school_21_community_bot_3.bot.handlers.search.get_inline_keyboard",
        return_value=mock_keyboard
    ):
        await role_selection_keyb(
            mock_message,
            state=mock_state,
            session=mock_session
        )

    mock_state.update_data.assert_any_call(offset=START_OFFSET)
    mock_state.update_data.assert_any_call(limit=LIMIT)
    mock_message.answer.assert_any_call(
        Messages.LETS_START,
        reply_markup=ReplyKeyboardRemove()
    )
    mock_message.answer.assert_any_call(
        Messages.WHOS_LOOKING_FOR,
        reply_markup=mock_keyboard
    )
    mock_state.set_state.assert_called_once_with(Search.waiting_for_role)


@pytest.mark.asyncio
async def test_choosing_a_role():
    """Тестирование фильтрации по роли."""
    # Создаем мок-объекты
    mock_user = create_mock_user()
    mock_chat = create_mock_chat()
    mock_callback_query = create_mock_message(mock_user, mock_chat)
    mock_state = AsyncMock(spec=FSMContext)
    mock_session = AsyncMock(spec=AsyncSession)

    mock_callback_query.data = "role_example"
    mock_callback_query.message = AsyncMock()
    mock_callback_query.message.answer = AsyncMock()

    mock_state.update_data = AsyncMock()
    mock_state.set_state = AsyncMock()

    mock_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Junior', callback_data='Junior'),
         InlineKeyboardButton(text='Lead', callback_data='Lead')],
        [InlineKeyboardButton(text='Middle', callback_data='Middle'),
         InlineKeyboardButton(text='Senior', callback_data='Senior')],
        [InlineKeyboardButton(text='Не важно', callback_data='Не важно'),
         InlineKeyboardButton(text='Стажер', callback_data='Стажер')],
        [InlineKeyboardButton(text='Назад', callback_data='Back')]
    ])

    with patch(
        "school_21_community_bot_3.bot.handlers.search.get_inline_keyboard",
        return_value=mock_keyboard
    ):
        await choosing_a_role(
            mock_callback_query,
            state=mock_state,
            session=mock_session
        )

    mock_state.update_data.assert_called_once_with(role="role_example")

    expected_message_text = Messages.WHAT_LEVEL
    mock_callback_query.message.answer.assert_called_once_with(
        expected_message_text,
        reply_markup=mock_keyboard
    )

    mock_callback_query.answer.assert_called_once()
    mock_state.set_state.assert_called_once_with(Search.waiting_for_level)


@pytest.mark.asyncio
async def test_go_to_searching_start(mock_objects):
    """Тестирование функции для обработки нажатия кнопки "Назад"."""
    mock_user, mock_chat, mock_message, mock_callback_query = mock_objects
    mock_callback_query.data = "back"
    mock_callback_query.message.answer = AsyncMock()
    mock_callback_query.answer = AsyncMock()
    mock_state = AsyncMock(spec=FSMContext)
    mock_session = AsyncMock(spec=AsyncSession)

    mock_state.update_data = AsyncMock()
    mock_state.set_state = AsyncMock()
    mock_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="golang разработчик",
            callback_data="golang разработчик"
        )]
    ])

    with patch(
        "school_21_community_bot_3.bot.handlers.search.get_inline_keyboard",
        return_value=mock_keyboard
    ):
        await go_to_searching_start(
            mock_callback_query,
            state=mock_state,
            session=mock_session
        )

    mock_callback_query.message.answer.assert_called_once_with(
        Messages.WHOS_LOOKING_FOR,
        reply_markup=mock_keyboard
    )
    mock_callback_query.answer.assert_called_once()
    mock_state.update_data.assert_called_once_with(offset=START_OFFSET)
    mock_state.set_state.assert_called_once_with(Search.waiting_for_role)


@pytest.mark.asyncio
async def test_back_to_begin(mock_objects):
    """Тестирование функции для обработки нажатия кнопки "В начало"."""
    mock_callback_query = AsyncMock()
    mock_callback_query.data = "to_begin"
    mock_callback_query.from_user.id = 123324
    mock_callback_query.answer = AsyncMock()

    mock_message = AsyncMock()
    mock_message.answer = AsyncMock()
    mock_session = AsyncMock()
    mock_state = AsyncMock(spec=FSMContext)
    keyboard_mock = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='Продолжить')]],
        resize_keyboard=True
    )
    with patch(
        "school_21_community_bot_3.bot.handlers.search.get_keyboard",
        return_value=keyboard_mock
    ):
        await back_to_begin(
            mock_callback_query,
            mock_session,
            state=mock_state
        )
