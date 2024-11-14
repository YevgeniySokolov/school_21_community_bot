import os

from dotenv import load_dotenv

load_dotenv()


class TestIntValues:

    TEAM_NAME_REPL = 16
    DESC_REPL = 64


class TestStrValues:

    DATABASE_URL = os.getenv("DATABASE_URL")
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHANNEL_ID = os.getenv("CHANNEL_ID")
    TEST_TELEGRAM_TOKEN = "test_telegram_token"
    TEST_CHANNEL_ID = -123456344
    TEST_INVITE_LINK = "https://t.me/joinchat/test_invite_link"
    ALEMBIC_CONFIG = os.getenv("ALEMBIC_CONFIG")


class TestMessages:

    ERROR_DATABASE_URL_NOT_SET = "DATABASE_URL не установлена."
    ERROR_ENV_VAR_NOT_SET = "Переменная {} не установлена в окружении."
    ERROR_DB_CONNECTION = "Ошибка подключения к базе данных: {}"
    INSUFFICIENT_RIGHTS_MSG = "Недостаточно прав для создания."
    DONT_CREATE_LINK_MSG = "Вы не можете создать ссылку на приглашение."
