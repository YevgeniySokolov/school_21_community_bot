import logging
import os
from datetime import datetime

import pytz
from dotenv import load_dotenv
from sqlalchemy import (BigInteger, Boolean, Column, DateTime, ForeignKey,
                        Integer, String)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from logger.logmessages import LogMessage
from settings import DATE_FORMAT

load_dotenv(override=True, verbose=True)
DATABASE_URL = os.getenv("DATABASE_URL")
CHANNEL_ID = os.getenv("CHANNEL_ID")
db_logger = logging.getLogger("DB_LOGGER")


# Создаем асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=True)

# Настройка сессии для работы с базой данных
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=True,
)

# Определение базовой модели
Base = declarative_base()
# Московский часовой пояс
moscow_tz = pytz.timezone('Europe/Moscow')


class User(Base):
    __tablename__ = "users"
    # Инкрементный ключ
    id = Column(Integer, primary_key=True, index=True)
    # получаем от бота telegram_id
    telegram_id = Column(BigInteger, unique=True, index=True)
    # telegram_username получаем от бота
    username = Column(String, unique=True, index=True)
    # SberID получаем от пользователя в Telegram
    sber_id = Column(String(256), unique=True)
    # Наименование команды
    team_name = Column(String(256))
    # Пользователь вводит уровень + роль
    role = Column(String(256))
    # Внешний ключ на уровень
    level_id = Column(Integer, ForeignKey("level.id"))
    # Вкратце описание, над чем работает человек
    description = Column(String(1024))
    registration_date = Column(
        DateTime, default=lambda: datetime.now(moscow_tz)
    )
    # Ник в Школе 21
    school21_nickname = Column(String(256), unique=True)
    # Пользователь админ
    is_admin = Column(Boolean, default=False)
    # Пользователь завершил регистрацию
    is_registered = Column(Boolean, default=False)
    # Первое незаполненное поле у пользователей, прервавших регистрацию
    field_not_filled = Column(String(64), default=None)

    # Определяем отношения с другими таблицами
    level = relationship("Level")

    # метод для упаковки в словарь, экспорт фикстур
    def to_dict(self):
        return {
            "id": self.id,
            "telegram_id": self.telegram_id,
            "username": self.username,
            "sber_id": self.sber_id,
            "team_name": self.team_name,
            "role": self.role,
            "level_id": self.level_id,
            "description": self.description,
            "registration_date": self.registration_date.strftime(
                DATE_FORMAT
            ) if self.registration_date else None,
            "school21_nickname": self.school21_nickname,
            "is_admin": self.is_admin,
            "is_registered": self.is_registered,
            "field_not_filled": self.field_not_filled
        }


class Level(Base):
    __tablename__ = "level"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)

    # метод для упаковки в словарь, экспорт фикстур
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }


class AdminSettings(Base):
    __tablename__ = "admin_settings"
    id = Column(Integer, primary_key=True, index=True)
    # Флаг, указывающий, зашифрована ли база данных
    is_encrypted = Column(Boolean, default=False)
    # Примерное поле для настройки бота (например, активация режима дебага)
    bot_debug_mode = Column(Boolean, default=False)
    # ID Telegram чата сообщества в формате строки
    community_chat_id = Column(String, unique=True)
    # Дата последнего изменения настроек
    last_updated = Column(DateTime, default=lambda: datetime.now(moscow_tz))

    # Telegram ID пользователя, который сделал последнее изменение
    updated_by = Column(BigInteger, ForeignKey("users.telegram_id"))

    # Связь с таблицей пользователей (администратор, который сделал изменение)
    updated_by_user = relationship("User", foreign_keys=[updated_by])


async def init_db():
    db_logger.info(LogMessage.START_INIT_DB)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Проверяем, есть ли данные в таблице Level

    async with AsyncSessionLocal() as session:
        result_level = await session.execute(select(Level))
        levels = result_level.scalars().all()
        if not levels:
            db_logger.info(LogMessage.PRESETTING_VALUES)
            # Если таблица Level пустая, добавляем дефолтные значения
            default_levels = [
                Level(id=1, name="Не важно"),
                Level(id=2, name="Junior"),
                Level(id=3, name="Middle"),
                Level(id=4, name="Senior"),
                Level(id=5, name="Lead"),
                Level(id=6, name="Стажер")
            ]
            session.add_all(default_levels)
            await session.commit()
            db_logger.info(LogMessage.JOB_IS_DONE)

        admin_settings = await session.execute(
            select(AdminSettings)
        )
        admin_settings = admin_settings.scalars().first()

        # Если запись не найдена или нужные поля равны NULL,
        # создадим новую запись с дефолтными значениями
        if not admin_settings:
            # Если записи вообще нет, создаем новую
            new_admin_settings = AdminSettings(
                is_encrypted=0,
                bot_debug_mode=0,
                community_chat_id=CHANNEL_ID,
            )
            session.add(new_admin_settings)
            await session.commit()
