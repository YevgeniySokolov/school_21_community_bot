import os
from unittest.mock import AsyncMock

import pytest
from aiogram.types import Message

from bot.messages import Messages
from bot.utils import download_file


@pytest.fixture
def setup_download_file(tmp_path):
    """Настройка сообщения и мока бота."""
    message = AsyncMock(spec=Message)
    message.document = AsyncMock()
    message.document.file_name = "test_dump_file.json"
    message.document.file_id = "12345"
    message.bot = AsyncMock()
    message.answer = AsyncMock()

    return message


@pytest.mark.asyncio
async def test_download_file(setup_download_file):
    """Тест успешной загрузки файла."""
    message = setup_download_file
    message.bot.get_file = AsyncMock(
        return_value=AsyncMock(file_path="path/to/file")
    )

    message.bot.download_file = AsyncMock(
        side_effect=lambda file_path,
        destination: os.makedirs(
            os.path.dirname(destination),
            exist_ok=True) or open(destination, 'w').close()
    )

    await download_file(message)

    assert message.bot.get_file.called
    assert message.bot.download_file.called
    assert os.path.exists(f"./temp/{message.document.file_name}")


@pytest.mark.asyncio
async def test_download_file_invalid_format(setup_download_file):
    """Тест неверного формата файла."""
    message = setup_download_file
    message.document.file_name = "test_dump_file.txt"

    await download_file(message)

    message.answer.assert_called_once_with(Messages.ERROR_FILE_FORMAT_MESSAGES)
    assert not os.path.exists(f"./temp/{message.document.file_name}")
