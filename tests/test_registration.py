from dataclasses import dataclass, field
from unittest.mock import AsyncMock, PropertyMock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import (Chat, KeyboardButton, Message, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove)
from sqlalchemy.ext.asyncio import AsyncSession

from .constants import TestIntValues
from bot.handlers.registration import (handle_join_community,
                                       handle_search_peers,
                                       process_activity_description,
                                       process_role, process_sber_id,
                                       process_school21_nickname,
                                       process_team_number, reg_action,
                                       send_welcome, skip_description_callback)
from bot.keyboards.keyboards import get_skip_inline_keyboard
from bot.messages import Messages
from bot.states.states import Registration
from database.models import User, moscow_tz


def create_mock_user(
        user_id=12345,
        telegram_id=987654321,
        username="test_username",
        sber_id="sber_id_example",
        team_name="Team Alpha",
        role="Developer",
        level_id=1,
        description="Working on project X",
        school21_nickname="school21_nickname_test",
        is_admin=False,
        is_registered=True,
        field_not_filled=None,
):
    """Создает мок-объект User."""
    return User(
        id=user_id,
        telegram_id=telegram_id,
        username=username,
        sber_id=sber_id,
        team_name=team_name,
        role=role,
        level_id=level_id,
        description=description,
        registration_date=moscow_tz,
        school21_nickname=school21_nickname,
        is_admin=is_admin,
        is_registered=is_registered,
        field_not_filled=field_not_filled,
    )


def create_mock_chat(chat_id=123456, chat_type="private"):
    """Создает мок-объект Chat."""
    return Chat(id=chat_id, type=chat_type)


def create_mock_message(user, chat):
    """Создает мок-объект Message."""
    mock_message = AsyncMock(spec=Message)
    mock_message.from_user = user
    mock_message.chat = chat
    mock_message.answer = AsyncMock()
    mock_message.reply = AsyncMock()
    return mock_message


@dataclass
class MockMessage:
    """Класс для имитации сообщения в тестах."""
    message_id: int
    from_user: User
    chat: Chat
    date: str
    text: str
    answer: AsyncMock = field(default_factory=AsyncMock)

    @property
    def message(self):
        return self

    async def reply(self, text: str):
        return await self.answer(text)


def compare_reply_keyboard_markup(rkm1, rkm2):
    """Сравнивает два объекта ReplyKeyboardMarkup по их содержимому."""
    is_equal = (
        rkm1.keyboard == rkm2.keyboard and
        rkm1.resize_keyboard == rkm2.resize_keyboard and
        rkm1.one_time_keyboard == rkm2.one_time_keyboard and
        rkm1.input_field_placeholder == rkm2.input_field_placeholder and
        rkm1.selective == rkm2.selective
    )
    if not is_equal:
        print(f"Сравнение не удалось: {rkm1} != {rkm2}")
    return is_equal


@pytest.mark.asyncio
async def test_send_welcome_registered_user():
    """Тест отправки приветственного сообщения
    для зарегистрированного пользователя."""
    mock_user = create_mock_user()
    mock_chat = create_mock_chat()
    mock_message = create_mock_message(mock_user, mock_chat)
    mock_state = AsyncMock()

    keyboard = [[KeyboardButton(text="Пройти аутентификацию")]]
    mock_message.reply_markup = ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )

    with patch(
        "school_21_community_bot_3.bot.utils.get_user_registered",
        return_value=True
    ):
        await send_welcome(event=mock_message, state=mock_state)
        assert mock_message.answer.call_count == 3
        calls = mock_message.answer.call_args_list
        assert calls[0][0][0] == Messages.WELCOME_MESSAGE
        assert compare_reply_keyboard_markup(
            calls[0][1]["reply_markup"],
            mock_message.reply_markup,
        )


@pytest.mark.asyncio
async def test_send_welcome_unregistered_user():
    """Тест отправки приветственного сообщения
    для незарегистрированного пользователя."""
    mock_user = create_mock_user()
    mock_chat = create_mock_chat()
    mock_message = create_mock_message(mock_user, mock_chat)
    mock_state = AsyncMock()

    with patch(
        "school_21_community_bot_3.bot.utils.get_user_registered",
        return_value=False
    ):
        await send_welcome(
            event=mock_message,
            state=mock_state,
            session=AsyncMock()
        )
        assert mock_message.answer.call_count == 3
        calls = mock_message.answer.call_args_list
        assert calls[0][0][0] == Messages.WELCOME_MESSAGE
        assert calls[1][0][0] == Messages.NOT_REGISTERED_MESSAGE
        assert calls[2][0][0] == Messages.AUTH_MESSAGE


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "is_admin, chat_type, expected_response",
    [
        # Администратор в приватном чате
        (True, "private", Messages.ENTER_NICK_SCHOOL_MESSAGE),
        # Не администратор в приватном чате
        (False, "private", Messages.ENTER_NICK_SCHOOL_MESSAGE),
        # Администратор в групповом чате (ожидается, что ответа не будет)
        (True, "group", None),
        # Не администратор в групповом чате (ожидается, что ответа не будет)
        (False, "group", None),
    ]
)
async def test_reg_action(is_admin, chat_type, expected_response):
    """Тест для проверки действия регистрации в
    зависимости от прав администратора и типа чата."""
    user = create_mock_user()
    chat = create_mock_chat(chat_id=1, chat_type=chat_type)
    mock_message = MockMessage(
        message_id=1,
        from_user=user,
        chat=chat,
        date="2024-11-11T00:00:00Z",
        text="Test_text",
    )

    mock_session = AsyncMock()
    mock_session.get_user_admin = AsyncMock(return_value=is_admin)
    mock_state = AsyncMock()

    await reg_action(mock_message, state=mock_state, session=mock_session)

    if expected_response is not None:
        mock_message.answer.assert_called_once_with(
            expected_response,
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        mock_message.answer.assert_not_called()


@pytest.mark.asyncio
async def test_process_school21_nickname_success():
    """Тест обработки никнейма Школы 21 с успешной валидацией."""
    mock_user = create_mock_user()
    mock_chat = create_mock_chat()
    mock_message = create_mock_message(mock_user, mock_chat)
    mock_message.text = "validnickname"
    mock_state = AsyncMock()
    mock_session = AsyncMock()

    with patch(
        "school_21_community_bot_3.bot.handlers.registration."
        "validate_and_update_state",
        # Успешная валидация
        return_value=True
    ), patch(
        "school_21_community_bot_3.bot.messages.Messages."
        "ENTER_SBER_ID_MESSAGE",
        new_callable=PropertyMock
    ) as mock_enter_sber_id_message:
        mock_enter_sber_id_message.return_value = (
            Messages.ENTER_SBER_ID_MESSAGE
        )
        await process_school21_nickname(
            mock_message,
            mock_state,
            session=mock_session
        )
        # Проверяем, что было отправлено сообщение с запросом SberID
        mock_message.answer.assert_called_once_with(
            Messages.ENTER_SBER_ID_MESSAGE
        )
        # Проверяем, что состояние было установлено на ожидание SberID
        mock_state.set_state.assert_called_once_with(
            Registration.waiting_for_sber_id
        )


@pytest.mark.asyncio
async def test_process_school21_nickname_validation_failure():
    """Тест обработки никнейма Школы 21 с неуспешной валидацией."""
    mock_message = AsyncMock()
    mock_message.text = 'invalid_nickname123'
    mock_state = AsyncMock()
    mock_session = AsyncMock()

    with patch(
        'school_21_community_bot_3.bot.handlers.registration.'
        'validate_and_update_state',
        new_callable=AsyncMock,
        # Неуспешная валидация
        return_value=False
    ):
        await process_school21_nickname(
            mock_message,
            mock_state,
            session=mock_session
        )
        # Проверяем, что сообщение не было отправлено
        mock_message.answer.assert_not_called()
        # Проверяем, что состояние не было изменено
        mock_state.set_state.assert_not_called()


@pytest.mark.asyncio
async def test_process_sber_id_success():
    """Тест обработки SberID с успешной валидацией."""
    mock_user = create_mock_user()
    mock_chat = create_mock_chat()
    mock_message = create_mock_message(mock_user, mock_chat)
    mock_message.text = "valid_sber_id"
    mock_state = AsyncMock()
    mock_session = AsyncMock()

    with patch(
        "school_21_community_bot_3.bot.handlers.registration."
        "validate_and_update_state",
        # Успешная валидация
        return_value=True
    ):
        await process_sber_id(
            mock_message,
            mock_state,
            session=mock_session
        )
        mock_message.answer.assert_called_once_with(
            Messages.ENTER_TEAM_MESSAGE
        )
        mock_state.set_state.assert_called_once_with(
            Registration.waiting_for_team_name
        )


@pytest.mark.asyncio
async def test_process_sber_id_validation_failure():
    """Тест обработки SberID с неуспешной валидацией."""
    mock_message = AsyncMock()
    mock_message.text = "невалид_sber_id"
    mock_state = AsyncMock()
    mock_session = AsyncMock()

    with patch(
        "school_21_community_bot_3.bot.handlers.registration."
        "validate_and_update_state",
        # Неуспешная валидация
        return_value=False
    ):
        await process_sber_id(
            mock_message,
            mock_state,
            session=mock_session
        )
        mock_message.answer.assert_not_called()
        mock_state.set_state.assert_not_called()


@pytest.mark.asyncio
async def test_process_team_name_success():
    """Тест обработки названия команды с успешной валидацией."""
    mock_user = create_mock_user()
    mock_chat = create_mock_chat()
    mock_message = create_mock_message(mock_user, mock_chat)
    mock_message.text = "valid_team_name"
    mock_state = AsyncMock()
    mock_session = AsyncMock()

    with patch(
        "school_21_community_bot_3.bot.handlers.registration."
        "validate_and_update_state",
        # Успешная валидация
        return_value=True
    ):
        await process_team_number(
            mock_message,
            mock_state,
            session=mock_session
        )
        mock_message.answer.assert_called_once_with(
            Messages.ENTER_ROLE_IN_TEAM
        )
        mock_state.set_state.assert_called_once_with(
            Registration.waiting_for_role_level
        )


@pytest.mark.asyncio
async def test_process_team_name_validation_failure():
    """Тест обработки названия команды с неуспешной валидацией."""
    mock_message = AsyncMock()
    mock_message.text = "invalid_team_name" * TestIntValues.TEAM_NAME_REPL
    mock_state = AsyncMock()
    mock_session = AsyncMock()

    with patch(
        "school_21_community_bot_3.bot.handlers.registration."
        "validate_and_update_state",
        # Неуспешная валидация
        return_value=False
    ):
        await process_team_number(
            mock_message,
            mock_state,
            session=mock_session
        )
        mock_message.answer.assert_not_called()
        mock_state.set_state.assert_not_called()


@pytest.mark.asyncio
async def test_process_role():
    """Тест обработки уровня роли."""
    mock_user = create_mock_user()
    mock_chat = create_mock_chat()
    mock_message = create_mock_message(mock_user, mock_chat)
    mock_message.text = "Test role level"
    mock_state = AsyncMock(spec=FSMContext)
    mock_session = AsyncMock(spec=AsyncSession)

    with patch(
        "school_21_community_bot_3.bot.handlers.registration."
        "validate_and_update_state",
        return_value=True
    ):
        await process_role(mock_message, mock_state, session=mock_session)

    mock_state.update_data.assert_any_call(role_level='Test role level')

    mock_message.answer.assert_called_once_with(
        Messages.ENTER_ABOUT,
        reply_markup=get_skip_inline_keyboard()
    )
    mock_state.set_state.assert_called_once_with(
        Registration.waiting_for_activity_description
    )


@pytest.mark.asyncio
async def test_skip_description_callback():
    """Тест обработки нажатия кнопки пропуска описания."""
    mock_callback_query = AsyncMock()
    mock_state = AsyncMock()
    mock_session = AsyncMock()
    await skip_description_callback(
        mock_callback_query,
        state=mock_state,
        session=mock_session
    )


@pytest.mark.asyncio
async def test_process_activity_description_skip():
    """Тест обработки описания при пропуске."""
    mock_message = AsyncMock()
    mock_state = AsyncMock()
    mock_session = AsyncMock()
    mock_state.get_data = AsyncMock(
        return_value={"activity_description": None}
    )
    await process_activity_description(
        mock_message,
        mock_state,
        session=mock_session
    )


@pytest.mark.asyncio
async def test_process_activity_description_validation_failure():
    """Тест обработки описания с неуспешной валидацией."""
    mock_message = AsyncMock()
    mock_message.text = "invalid_description" * TestIntValues.DESC_REPL
    mock_state = AsyncMock()
    mock_session = AsyncMock()

    with patch(
        "school_21_community_bot_3.bot.handlers.registration."
        "validate_and_update_state",
        # Неуспешная валидация
        return_value=False
    ):
        await process_activity_description(
            mock_message,
            mock_state,
            session=mock_session
        )
        mock_message.answer.assert_not_called()
        mock_state.set_state.assert_not_called()


@pytest.mark.asyncio
async def test_handle_join_community():
    """Тест обработки нажатия кнопки 'Присоединиться к комьюнити'."""
    mock_callback_query = AsyncMock()
    mock_callback_query.from_user.id = 123456
    mock_callback_query.from_user.username = "Test_user"
    mock_callback_query.message = AsyncMock()
    mock_state = AsyncMock()
    mock_session = AsyncMock()
    user_data = {
        "role_level": "test_role_level"
    }
    mock_state.get_data = AsyncMock(return_value=user_data)
    # Установка моков для функций
    with patch(
        "school_21_community_bot_3.bot.handlers.registration."
        "parse_level_and_role",
        return_value=(1, "test_role")
    ), patch(
        "school_21_community_bot_3.bot.handlers.registration."
        "save_or_update_user",
        return_value=None
    ), patch(
        "school_21_community_bot_3.bot.handlers.registration."
        "send_invite_link",
        return_value=None
    ):
        await handle_join_community(
            mock_callback_query,
            state=mock_state,
            session=mock_session
        )


@pytest.mark.asyncio
async def test_handle_search_peers():
    """Тест обработки нажатия кнопки 'Поиск пользователей'."""
    mock_callback_query = AsyncMock()
    mock_callback_query.from_user.id = 123456
    mock_callback_query.from_user.username = "Test_user"
    mock_callback_query.message = AsyncMock()
    mock_state = AsyncMock()
    mock_session = AsyncMock()
    user_data = {
        "role_level": "test_role_level"
    }
    mock_state.get_data = AsyncMock(return_value=user_data)

    with patch(
        "school_21_community_bot_3.bot.handlers.registration."
        "parse_level_and_role",
        return_value=(1, "test_role")
    ), patch(
        "school_21_community_bot_3.bot.handlers.registration."
        "save_or_update_user",
        return_value=None
    ):
        await handle_search_peers(
            mock_callback_query,
            session=mock_session,
            state=mock_state
        )
