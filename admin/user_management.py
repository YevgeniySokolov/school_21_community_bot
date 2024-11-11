
import os
import sys
from typing import List, Optional

import streamlit as st
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from database.models import User

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Асинхронная функция для получения всех пользователей
async def fetch_all_users(db: AsyncSession) -> List[User]:
    """
    Получение всех пользователей из базы данных
    с загрузкой связанных уровней.
    """
    # Используем selectinload для загрузки связанных объектов (уровней)
    result = await db.execute(
        select(User).options(selectinload(User.level))
    )
    return result.scalars().all()


async def fetch_registered_users(db: AsyncSession) -> List[User]:
    """
    Получение списка зарегистрированных пользователей из базы данных
    с загрузкой связанных уровней.
    """
    # Используем selectinload для загрузки связанных объектов (уровней)
    result = await db.execute(
        select(User)
        .options(selectinload(User.level))
        .where(User.is_registered.is_(True))
    )
    return result.scalars().all()


async def fetch_unregistered_users(db: AsyncSession) -> List[User]:
    """
    Получение списка незарегистрированных пользователей из базы данных
    с загрузкой связанных уровней.
    """
    # Используем selectinload для загрузки связанных объектов (уровней)
    result = await db.execute(
        select(User)
        .options(selectinload(User.level))
        .where(User.is_registered.is_(False))
    )
    return result.scalars().all()


async def fetch_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """
    Получение пользователя из базы данных по его id.
    """
    result = await db.execute(
        select(User)
        .options(selectinload(User.level))
        .where(User.id == user_id)
    )
    # Получаем пользователя или None
    user = result.scalar_one_or_none()
    return user


async def fetch_user_by_telegram_id(
        db: AsyncSession, telegram_id: int
) -> Optional[User]:
    """
    Получение пользователя из базы данных по его Telegram ID.
    """
    result = await db.execute(
        select(User)
        .options(selectinload(User.level))
        .where(User.telegram_id == telegram_id)
    )
    # Получаем пользователя или None
    user = result.scalar_one_or_none()
    return user


async def update_metrics(session: AsyncSession):
    """
    Асинхронная функция для обновления метрик пользователей в сессии.
    Функция получает данные о зарегистрированных и незавершивших регистрацию
    пользователях из базы данных и сохраняет их в `st.session_state`.
    """
    registered_users = await fetch_registered_users(session)
    abandoned_users = await fetch_unregistered_users(session)
    st.session_state.registered_users = len(registered_users)
    st.session_state.abandoned_users = len(abandoned_users)


async def incomplete_registration_stats(db: AsyncSession):
    """
    Извлекает статистику по незарегистрированным пользователям.
    Args:
        db: Асинхронная сессия SQLAlchemy.
    Returns:
        Словарь со статистикой или None в случае ошибки.
    """
    # Получаем статистику по незарегистрированным пользователям
    stmt = (
        select(User.field_not_filled, func.count().label('count'))
        .where(User.is_registered.is_(False))
        .group_by(User.field_not_filled)
    )
    result = await db.execute(stmt)
    rows = result.fetchall()
    if not rows:
        return {}
    # Получаем общее количество незарегистрированных пользователей
    total_unregistered_stmt = (
        select(func.count())
        .where(User.is_registered.is_(False))
    )
    total_unregistered = await db.execute(total_unregistered_stmt)
    total_unregistered_count = total_unregistered.scalar()
    # Формируем статистику
    stats = {}
    for row in rows:
        field_value = row[0]  # Значение поля
        count = row[1]  # Количество пользователей
        percentage = (
            (count / total_unregistered_count) * 100
            if total_unregistered_count > 0
            else 0
        )
        percentage = round(percentage, 2)
        stats[field_value] = (count, percentage)

    return stats


async def registration_stats_by_date(db: AsyncSession):
    """
    Извлекает статистику регистрации пользователей по дате (без учета времени),
    корректно считая зарегистрированных пользователей.
    """
    # Подзапрос для подсчета зарегистрированных пользователей на каждую дату
    registered_users_subquery = (
        select(
            func.date(User.registration_date).label("registration_date"),
            func.count().label("registered_count")
        )
        .where(User.is_registered)
        .group_by(func.date(User.registration_date))
    ).subquery()

    # Основной запрос
    stmt = (
        select(
            func.date(User.registration_date).label("registration_date"),
            func.count().label("total_users"),
            registered_users_subquery.c
            .registered_count.label("registered_users")
        )
        .outerjoin(
            registered_users_subquery,
            func.date(User.registration_date) == registered_users_subquery.c
            .registration_date
        )
        .group_by(
            func.date(User.registration_date),
            registered_users_subquery.c.registered_count
        )
    )

    result = await db.execute(stmt)
    rows = result.fetchall()
    if not rows:
        return {}
    stats = {}
    for registration_date, total_users, registered_users in rows:
        unregistered_users = total_users - (registered_users or 0)
        conversion_rate = (
            ((registered_users or 0) / total_users) * 100
            if total_users > 0 else 0
        )
        conversion_rate = round(conversion_rate, 2)
        stats[registration_date] = {
            "total_users": total_users,
            "registered_users": registered_users or 0,
            "unregistered_users": unregistered_users,
            "conversion_rate": conversion_rate,
        }
    return stats
