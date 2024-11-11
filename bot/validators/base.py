import re

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database.models import User


async def validate_length(
        value: str,
        min_len: int,
        max_len: int,
        error_message: str
):
    """Проверка длины строки."""
    if len(value) < min_len or len(value) > max_len:
        return error_message
    return None


async def validate_pattern(
        value: str,
        pattern: str,
        error_message: str
):
    """Проверка соответствия строки паттерну."""
    if not re.match(pattern, value):
        return error_message
    return None


async def validate_existence(
        value: str,
        session: AsyncSession,
        error_message: str,
        field_name: str
):
    """Проверка существования значения в базе данных по указанному полю."""
    query = await session.execute(
        select(User).where(getattr(User, field_name) == value)
    )
    existing_user = query.scalar()
    if existing_user and existing_user.is_registered:
        return error_message
    return None


async def validate_and_update_state(
        message: Message,
        state: FSMContext,
        validation_func,
        next_state: str,
        session: AsyncSession
):
    """Осуществление валидации."""
    validation_error = await validation_func(message.text, session)
    if validation_error:
        await message.reply(validation_error)
        return False
    await state.update_data(**{next_state: message.text})
    return True
