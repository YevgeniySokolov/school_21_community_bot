import os
import sys
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from database.models import Level, User

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def add_user(
    db: AsyncSession,
    telegram_id: int,
    username: str,
    sber_id: str,
    team_name: str,
    level_id: int,
    description: str,
    registration_date: datetime,
    school21_nickname: str,
    is_admin: bool,
    is_registered: bool,
    role: str,
) -> User:
    """
    Добавление нового пользователя в базу данных.
    """
    new_user = User(
        telegram_id=telegram_id,
        username=username,
        sber_id=sber_id,
        team_name=team_name,
        level_id=level_id,
        description=description,
        registration_date=registration_date,
        school21_nickname=school21_nickname,
        is_admin=is_admin,
        is_registered=is_registered,
        role=role,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_user(
        db: AsyncSession, user_id: int, updated_user: Dict[str, Any]
) -> bool:
    """
    Редактирование пользователя.
    """
    try:
        async with db.begin():
            result = await db.execute(
                select(User)
                .options(selectinload(User.level))
                .where(User.id == user_id)
            )
            user = result.scalar()
            if user:
                changes_made = False
                for key, value in updated_user.items():
                    if getattr(user, key) != value:  # Проверка на изменения
                        setattr(user, key, value)
                        changes_made = True
                if changes_made:  # Если изменения были
                    return True
                else:
                    print("Нет изменений для обновления.")
                    return False
            else:
                print(f"Пользователь с ID {user_id} не найден.")
                return False
    except SQLAlchemyError as e:
        print(f"Ошибка при обновлении пользователя: {e}")
        return False


async def delete_user_by_telegram_id(
        db: AsyncSession, telegram_id: str
) -> bool:
    """
    Удаление пользователя по telegram_id.
    """
    async with db.begin():
        result = await db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user:
            await db.execute(delete(User).where(User.id == user.id))
            await db.commit()
            return True
        else:
            return False


async def get_level_id_by_level(level: str, db: AsyncSession) -> int:
    """
    Получение идентификатора уровня по его названию.
    """
    result = await db.execute(select(Level).filter_by(name=level))
    level_instance = result.scalar()
    if level_instance:
        return level_instance.id
    else:
        raise ValueError("Уровень не найден.")


def get_user_counts_by_level(users):
    """
    Подсчитывает количество пользователей по уровням.
    Принимает список пользователей и возвращает словарь,
    где ключами являются названия уровней, а значениями —
    количество пользователей на каждом уровне.
    """
    level_counts = {}
    for user in users:
        level_id = user.level.name
        if level_id in level_counts:
            level_counts[level_id] += 1
        else:
            level_counts[level_id] = 1
    return level_counts


async def get_telegram_id(username: str, db: AsyncSession):
    """
    Получает Telegram ID пользователя по username.
    """
    result = await db.execute(
        select(User.telegram_id).where(User.username == username)
    )
    user_telegram_id = result.scalar_one_or_none()
    return user_telegram_id


async def is_user_admin(username: str, db: AsyncSession) -> bool:
    """
    Проверяет, является ли пользователь администратором по username.
    """
    result = await db.execute(
        select(User.is_admin).where(User.username == username)
    )
    is_admin = result.scalar_one_or_none()
    return is_admin if is_admin is not None else False