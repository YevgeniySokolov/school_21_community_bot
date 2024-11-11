from functools import wraps

from aiogram.enums import ChatType
from aiogram.types import Message

from bot.messages import Messages
from bot.utils import get_user_admin
from database.models import AsyncSessionLocal


def db_session_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with AsyncSessionLocal() as session:
            # Передаем сессию под ключом session
            kwargs['session'] = session
            return await func(*args, **kwargs)
    return wrapper


def admin_required(handler):
    @wraps(handler)
    async def wrapper(message: Message, *args, **kwargs):
        session = kwargs.get('session')
        if session is None:
            raise ValueError(Messages.ERROR_BD_CHECK)
        is_admin = await get_user_admin(session, message.from_user.id)

        if not is_admin:
            await message.answer(Messages.NOT_HAVE_ADMIN_RIGHTS)
            return

        # Вызываем основной обработчик с оригинальными аргументами
        return await handler(message, *args, **kwargs)
    return wrapper


def private_only(handler):
    @wraps(handler)
    async def wrapper(event, *args, **kwargs):
        # Проверяем, является ли событие сообщением или обратным вызовом
        chat = event.chat if isinstance(event, Message) else event.message.chat
        # Проверяем, что чат приватный
        if chat.type != ChatType.PRIVATE:
            return
        # Если чат приватный, вызываем основной обработчик
        return await handler(event, *args, **kwargs)
    return wrapper
