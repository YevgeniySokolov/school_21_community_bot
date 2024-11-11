import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from dotenv import load_dotenv

from logger.logmessages import LogMessage

load_dotenv(override=True, verbose=True)
bot_logger = logging.getLogger("BOT_LOGGER")

TELEGRAM_TOKEN: str = os.getenv('TELEGRAM_TOKEN')

bot = Bot(token=TELEGRAM_TOKEN)
# Хранилище для состояний пользователей
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.callback_query.middleware(CallbackAnswerMiddleware())
dp.callback_query.middleware(
    CallbackAnswerMiddleware(
        pre=True, text="Принято!", show_alert=False
    )
)
bot_logger.info(LogMessage.MIDDLEWARES)
