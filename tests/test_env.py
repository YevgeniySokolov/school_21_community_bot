import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from .constants import TestMessages, TestStrValues


def test_environment_variables():
    """Тест на наличие необходимых переменных окружения."""
    required_vars = [
        TestStrValues.TELEGRAM_TOKEN,
        TestStrValues.CHANNEL_ID,
        TestStrValues.ALEMBIC_CONFIG
    ]
    for var in required_vars:
        assert var is not None, TestMessages.ERROR_ENV_VAR_NOT_SET.format(var)


@pytest.mark.asyncio
async def test_database_connection():
    """Тест для проверки подключения к базе данных."""
    assert TestStrValues.DATABASE_URL is not None, (
        TestMessages.ERROR_DATABASE_URL_NOT_SET
    )

    try:
        engine = create_async_engine(TestStrValues.DATABASE_URL, echo=True)
        async with engine.begin():
            pass
    except Exception as e:
        pytest.fail(TestMessages.ERROR_DB_CONNECTION.format(e))
    finally:
        await engine.dispose()
        del engine
