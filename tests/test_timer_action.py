from unittest.mock import ANY, AsyncMock, patch

import pytest
from aiogram.types import Message

from bot.messages import Messages
from bot.utils import timer_action


@pytest.fixture
def setup_timer_action():
    """Фикстура для настройки сообщения, состояния и сессии."""
    message = AsyncMock(spec=Message)
    message.from_user = AsyncMock()
    message.from_user.id = 12345344
    message.from_user.username = "test_user"
    message.answer = AsyncMock()
    state = AsyncMock()
    session = AsyncMock()
    return message, state, session


async def mock_check_user_exists(session, exists):
    """Мок для проверки существования пользователя."""
    session.query = AsyncMock()
    session.query.return_value.count.return_value = 1 if exists else 0


async def mock_user_actions(session, exists):
    """Мок для действий с пользователем."""
    user_mock = AsyncMock()
    user_mock.telegram_id = 12345344
    return user_mock


async def mock_parse_level_and_role(session):
    """Мок для парсинга уровня и роли."""
    return (1, "DevOps")


@pytest.mark.asyncio
async def test_timer_action_user_exists(setup_timer_action):
    """Тест для случая, когда пользователь существует."""
    message, state, session = setup_timer_action
    state.get_data.return_value = {
        "role_level": "Middle",
        "sber_id": "123456",
        "school21_nickname": "nickname",
        "team_name": "team",
        "activity_description": "description"
    }

    await mock_check_user_exists(session, True)

    with patch(
        "bot.utils.parse_level_and_role",
        new_callable=AsyncMock
    ) as mock_parse:
        mock_parse.return_value = await mock_parse_level_and_role(session)
        user_action_mock = await mock_user_actions(session, True)

        with patch(
            "bot.utils.update_user",
            new_callable=AsyncMock
        ) as mock_update_user:
            mock_update_user.return_value = user_action_mock

            with patch("asyncio.sleep", return_value=None):
                await timer_action(message, state, session)

            mock_update_user.assert_called_once()
            message.answer.assert_called_once_with(
                Messages.USER_BREAKE_OUT_REGISTRATION,
                reply_markup=ANY
            )


@pytest.mark.asyncio
async def test_timer_action_user_does_not_exist(setup_timer_action):
    """Тест для случая, когда пользователь не существует."""
    message, state, session = setup_timer_action
    state.get_data.return_value = {
        "role_level": "Junior",
        "sber_id": None,
        "school21_nickname": None,
        "team_name": None,
        "activity_description": None
    }

    await mock_check_user_exists(session, False)

    with patch(
        "bot.utils.parse_level_and_role",
        new_callable=AsyncMock
    ) as mock_parse:
        mock_parse.return_value = await mock_parse_level_and_role(session)
        user_action_mock = await mock_user_actions(session, False)

        with patch(
            "bot.utils.update_user",
            new_callable=AsyncMock
        ) as mock_update_user:
            mock_update_user.return_value = user_action_mock

            with patch("asyncio.sleep", return_value=None):
                await timer_action(message, state, session)

            mock_update_user.assert_called_once()
            message.answer.assert_called_once_with(
                Messages.USER_BREAKE_OUT_REGISTRATION,
                reply_markup=ANY
            )


@pytest.mark.asyncio
async def test_timer_action_with_empty_fields(setup_timer_action):
    """Тест для случая с пустыми полями."""
    message, state, session = setup_timer_action
    state.get_data.return_value = {
        "role_level": None,
        "sber_id": None,
        "school21_nickname": None,
        "team_name": None,
        "activity_description": None
    }

    await mock_check_user_exists(session, False)

    with patch(
        "bot.utils.parse_level_and_role",
        new_callable=AsyncMock
    ) as mock_parse:
        mock_parse.return_value = await mock_parse_level_and_role(session)
        user_action_mock = await mock_user_actions(session, False)

        with patch(
            "bot.utils.update_user",
            new_callable=AsyncMock
        ) as mock_update_user:
            mock_update_user.return_value = user_action_mock

            with patch("asyncio.sleep", return_value=None):
                await timer_action(message, state, session)

            mock_update_user.assert_called_once()
            message.answer.assert_called_once_with(
                Messages.USER_BREAKE_OUT_REGISTRATION,
                reply_markup=ANY
            )
