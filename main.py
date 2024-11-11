import asyncio
import logging

from aiogram.methods.delete_webhook import DeleteWebhook
from dotenv import find_dotenv, load_dotenv

from bot.bot import bot, dp
from bot.handlers.admin import router as adm_router
from bot.handlers.registration import router as reg_router
from bot.handlers.search import router as srch_router
from database.models import init_db
from logger.logger import configure_logging
from logger.logmessages import LogMessage

load_dotenv(find_dotenv(), override=True, verbose=True)


class StartupMiddleware:
    def __init__(self):
        self.initialized = False

    async def __call__(self, handler, event, data):
        if not self.initialized:
            await init_db()
            self.initialized = True
        return await handler(event, data)


async def main():
    # Регистрируем роутеры
    dp.include_router(reg_router)
    dp.include_router(srch_router)
    dp.include_router(adm_router)
    main_logger.debug(LogMessage.ROUTERS)

    # Добавляем middleware для выполнения при старте
    dp.message.middleware(StartupMiddleware())

    # Чтобы бот не реагировал на обновления в Телеграме, пока был выключен
    await bot(DeleteWebhook(drop_pending_updates=True))
    main_logger.debug(LogMessage.BOT_UP)

    # Запуск бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    configure_logging()
    main_logger = logging.getLogger('MAIN_LOGGER')
    main_logger.info(LogMessage.START_MSG)
    asyncio.run(main())
