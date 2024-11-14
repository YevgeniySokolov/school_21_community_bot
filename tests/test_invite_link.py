from unittest.mock import ANY, AsyncMock, MagicMock

import pytest
from aiogram.exceptions import TelegramBadRequest

from .constants import TestMessages, TestStrValues
from bot.utils import create_invite_link, send_invite_link


@pytest.mark.asyncio
async def test_create_invite_link():
    """Тест для функции создания временной ссылки на приглашение в группу."""
    bot = AsyncMock()
    bot.create_chat_invite_link.return_value = MagicMock(
        invite_link=TestStrValues.TEST_INVITE_LINK
    )

    invite_link = await create_invite_link(
        bot,
        TestStrValues.TEST_CHANNEL_ID
    )

    assert invite_link == TestStrValues.TEST_INVITE_LINK
    bot.create_chat_invite_link.assert_called_once_with(
        chat_id=TestStrValues.TEST_CHANNEL_ID,
        expire_date=ANY,
        member_limit=1
    )


@pytest.mark.asyncio
async def test_send_invite_link_success():
    """Тест для успешной отправки ссылки на приглашение в чат."""
    bot = AsyncMock()
    message = AsyncMock()
    bot.create_chat_invite_link.return_value = MagicMock(
        invite_link=TestStrValues.TEST_INVITE_LINK
    )

    result = await send_invite_link(bot, message)

    assert result == TestStrValues.TEST_INVITE_LINK


@pytest.mark.asyncio
async def test_send_invite_link_error():
    """Тест для обработки ошибки при отправке ссылки на приглашение в чат."""
    bot = AsyncMock()
    message = AsyncMock()
    bot.create_chat_invite_link.side_effect = TelegramBadRequest(
        TestMessages.DONT_CREATE_LINK_MSG,
        TestMessages.INSUFFICIENT_RIGHTS_MSG
    )
    result = await send_invite_link(bot, message)

    assert result is None
    message.answer.assert_called_once()
