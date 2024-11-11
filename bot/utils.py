import asyncio
import json
import logging
import os
import re

import aiofiles
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ChatInviteLink, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from bot.keyboards.keyboards import get_buttons, get_card_button
from bot.messages import Buttons, Messages
from database.models import Level, User
from logger.logmessages import LogMessage
from settings import (CHANNEL_ID, START_OFFSET, STATES_COLLECTION,
                      TIMER_USER_STEP)

hndlr_logger = logging.getLogger('HNDLR_LOGGER')


async def timer_action(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    """
    Функция включает таймер на время, определенное константой TIMER_USER_STEP.
    Таймер ожидает, когда пользователь пройдёт дальше по регистрации.
    Если нет движений, через TIMER_USER_STEP
    в базу данных записывается пользователь со всеми заполненными полями,
    в незаполненные подаётся значение "Пусто" или 0, в поле is_registered
    записывается False, в поле field_not_filled указывается то поле
    базы данных, перед которым пользователь остановился.
    Если в базе данных уже присутствует пользователь, запись обновляется.
    """
    await asyncio.sleep(TIMER_USER_STEP * 3600)
    await message.answer(Messages.USER_BREAKE_OUT_REGISTRATION)
    data = await state.get_data()

    field_not_filled = next(
        (state_name for state_name in STATES_COLLECTION
            if state_name not in data),
        None
    )

    if data.get('role_level'):
        level_id, role = await parse_level_and_role(
            data['role_level'], session
        )
    telegram_id = message.from_user.id
    username = message.from_user.username
    sber_id = data.get('sber_id') if data.get('sber_id') else 'Пусто'
    school21_nickname = (data.get('school21_nickname')
                         if data.get('school21_nickname') else 'Пусто')
    team_name = data.get('team_name') if data.get('team_name') else 'Пусто'
    role = role if data.get('role_level') else 'Пусто'
    level_id = level_id if data.get('role_level') else 1
    description = (
        data.get('activity_description')
        if data.get('activity_description')
        else 'Пусто'
    )
    is_registered = False
    field_not_filled = field_not_filled
    if await check_user_exists(session, telegram_id):
        await update_user(
            session,
            telegram_id=telegram_id,
            username=username,
            sber_id=sber_id,
            school21_nickname=school21_nickname,
            team_name=team_name,
            role=role,
            level_id=level_id,
            description=description,
            is_registered=is_registered,
            field_not_filled=field_not_filled,
        )
        await state.clear()
    else:
        await add_user(
            session,
            telegram_id=telegram_id,
            username=username,
            sber_id=sber_id,
            school21_nickname=school21_nickname,
            team_name=team_name,
            role=role,
            level_id=level_id,
            description=description,
            is_registered=is_registered,
            field_not_filled=field_not_filled,
        )
        await state.clear()


# Функция для создания временной ссылки на приглашение в группу
async def create_invite_link(bot, chat_id):
    invite_link: ChatInviteLink = await bot.create_chat_invite_link(
        chat_id=chat_id,
        # expire_date=int(time.time()) + (3600 * TIME_EXPIRE_HOUR),
        member_limit=1,  # Лимит на одного пользователя
    )
    return invite_link.invite_link


async def send_invite_link(bot, message):
    """Создать и отправить приглашение в чат с обработкой ошибок."""
    try:
        invite_link = await create_invite_link(bot, CHANNEL_ID)
        return invite_link
    except TelegramBadRequest as error_rights:
        # Обработка ошибки, если недостаточно прав для создания ссылки
        await message.answer(
            Messages.ERROR_LINK_RIGHTS.format(error_rights=error_rights)
        )
        hndlr_logger.error(LogMessage.ERROR.format(error_rights))
        return None


async def save_or_update_user(
    session, telegram_id, telegram_name, user_data, role, level_id
):
    """Добавить или обновить пользователя в базе данных."""
    if await check_user_exists(session, telegram_id):
        await update_user(
            session, telegram_id=telegram_id, username=telegram_name,
            sber_id=user_data['sber_id'],
            school21_nickname=user_data['school21_nickname'],
            team_name=user_data['team_name'], role=role, level_id=level_id,
            description=user_data['activity_description'], is_registered=True,
            field_not_filled=False,
        )
    else:
        await add_user(
            session, telegram_id=telegram_id, username=telegram_name,
            sber_id=user_data['sber_id'],
            school21_nickname=user_data['school21_nickname'],
            team_name=user_data['team_name'], role=role, level_id=level_id,
            description=user_data['activity_description'], is_registered=True,
            field_not_filled=False,
        )


# Функция шифрования по ключу
def xor_encr_decr(text, key) -> str:
    if text is None:
        return None

    key_length = len(key)
    return ''.join(
        chr(ord(char) ^ ord(key[i % key_length]))
        for i, char in enumerate(text)
    )


# Получение записи зарегистрированного пользователя
async def get_user_registered(db: AsyncSession, telegram_id: int) -> bool:
    # Выполняем запрос для получения информации по пользователю
    result = await db.execute(
        select(
            User.is_registered
        ).filter_by(
            telegram_id=telegram_id
        )
    )
    # Преобразуем результат в список объектов
    user_is_registered = result.scalar_one_or_none()
    return user_is_registered or False


# Проверка наличия прав администратора
async def get_user_admin(db: AsyncSession, telegram_id: int) -> bool:
    # Выполняем запрос для получения информации по пользователю
    result = await db.execute(
        select(
            User.is_admin
        ).filter_by(
            telegram_id=telegram_id
        )
    )
    user_is_admin = result.scalar_one_or_none()
    return user_is_admin or False


async def add_user(
    db: AsyncSession,
    telegram_id: int,
    username: str,
    sber_id: str,
    school21_nickname: str,
    team_name: str,
    role: str,
    level_id: int,
    description: str,
    is_registered: bool,
    field_not_filled: str,
) -> User:
    new_user = User(
        telegram_id=telegram_id,
        username=username,
        sber_id=sber_id,
        school21_nickname=school21_nickname,
        team_name=team_name,
        role=role,
        level_id=level_id,
        description=description,
        is_registered=is_registered,
        field_not_filled=field_not_filled,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def check_user_exists(
    db: AsyncSession,
    telegram_id: int
) -> bool:
    result = await db.execute(select(User).where(
        User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none() is not None


async def update_user(
    db: AsyncSession,
    telegram_id: int,
    username: str,
    sber_id: str,
    school21_nickname: str,
    team_name: str,
    role: str,
    level_id: int,
    description: str,
    is_registered: bool,
    field_not_filled: str,
):
    result = await db.execute(
        select(User).where(
            User.telegram_id == telegram_id)
    )
    updating_user = result.scalar()
    updating_user.telegram_id = telegram_id
    updating_user.username = username
    updating_user.sber_id = sber_id
    updating_user.school21_nickname = school21_nickname
    updating_user.team_name = team_name
    updating_user.role = role
    updating_user.level_id = level_id
    updating_user.description = description
    updating_user.is_registered = is_registered
    updating_user.field_not_filled = field_not_filled
    await db.commit()
    await db.refresh(updating_user)
    return updating_user


async def create_orm_dump(session: AsyncSession, dump_file_path: str):
    # Словарь для хранения данных из таблиц
    all_data = {
        "users": [],
        "levels": [],
    }

    # Дамп данных из таблицы User
    result_users = await session.execute(select(User))
    users = result_users.scalars().all()
    all_data["users"] = [user.to_dict() for user in users]

    # Дамп данных из таблицы Level
    result_levels = await session.execute(select(Level))
    levels = result_levels.scalars().all()
    all_data["levels"] = [level.to_dict() for level in levels]

    # Запись данных в JSON файл
    with open(dump_file_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False, default=str)


# для парсера роли+уровня
async def parse_level_and_role(input_str, session: AsyncSession):
    # Получаем все уровни из базы данных с их идентификаторами
    result = await session.execute(select(Level.id, Level.name))
    # Создаем словарь {название уровня: id уровня}
    levels = {row[1]: row[0] for row in result.fetchall()}

    # Создаем регулярное выражение на основе названий уровней из базы
    level_pattern = rf"^({'|'.join(map(re.escape, levels.keys()))})\b"

    # Ищем уровень в начале строки
    match = re.match(level_pattern, input_str)

    # Уровень найден
    if match:
        level_name = match.group(0)
        # Получаем id уровня из словаря, если нет — 0
        level_id = levels.get(level_name, 0)
        # Всё, что после уровня, является ролью
        role = input_str[len(level_name):].strip()
    else:
        level_id = 1  # Если уровень не найден, ставим "Не важно"
        # Вся строка — это роль
        role = input_str.strip()

    return level_id, role


# Получение списка пользователей с пагинацией
async def get_user_list(
    session: AsyncSession,
    level_id: int,
    offset: int,
    limit: int,
    role: str,
):
    if level_id == 1:
        user_list = await session.execute(
            select(User.id, User.sber_id, User.team_name).where(
                User.role == role
            )
        )
        limited_user_list = await session.execute(
            select(User.id, User.sber_id, User.team_name).where(
                User.role == role
            ).offset(offset).limit(limit)
        )
    else:
        user_list = await session.execute(
            select(User.id, User.sber_id, User.team_name).where(
                User.level_id == level_id, User.role == role
            )
        )
        limited_user_list = await session.execute(
            select(User.id, User.sber_id, User.team_name).where(
                User.level_id == level_id, User.role == role
            ).offset(offset).limit(limit)
        )
    return limited_user_list.all(), len(user_list.all())


async def download_file(
    message: Message
):
    # Создаем временную директорию, если её нет
    os.makedirs("./temp", exist_ok=True)
    file_path = f"./temp/{message.document.file_name}"

    if not message.document.file_name.endswith(".json"):
        await message.answer(Messages.ERROR_FILE_FORMAT_MESSAGES)
        return None

    file_id = message.document.file_id
    try:
        file = await message.bot.get_file(file_id)
        await message.bot.download_file(file.file_path, destination=file_path)
    except Exception as error_file:
        await message.answer(
            Messages.ERROR_FILE_DOWNLOAD.format(error_file=error_file)
        )
        return None

    # Проверка, создался ли файл
    if not os.path.exists(file_path):
        await message.answer(Messages.ERROR_NOT_LOAD_FIXTURE_FILE)
        return None
    return file_path


async def load_json_data(file_path):
    # Чтение JSON и проверка данных
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
        content = await f.read()
        return json.loads(content)


async def load_existing_data(session):
    existing_users = {
        user.telegram_id: user for user in (
            await session.execute(select(User))
        ).scalars()
    }
    existing_levels = {
        level.id: level for level in (
            await session.execute(select(Level))
        ).scalars()
    }
    return existing_users, existing_levels


def find_duplicates(data, field):
    field_values = [user.get(field) for user in data["users"] if field in user]
    return [
        value for value in set(field_values) if field_values.count(value) > 1
    ]


async def get_user_db_data(db: AsyncSession, telegram_id: int) -> bool:
    # Выполняем запрос для получения информации по пользователю
    result = await db.execute(
        select(
            User
        ).filter_by(
            telegram_id=telegram_id
        )
    )
    # Получаем объект пользователя
    existing_user = result.scalar_one_or_none()
    user_fields = []
    # Добавляем данные из БД, если они не заполнены дефолтными значениями
    existing_user.school21_nickname != 'Пусто' and (
        user_fields.append(existing_user.school21_nickname))
    existing_user.sber_id != 'Пусто' and (
        user_fields.append(existing_user.sber_id))
    existing_user.team_name != 'Пусто' and (
        user_fields.append(existing_user.team_name))
    existing_user.role != 'Пусто' and (
        user_fields.append(existing_user.role))
    existing_user.description != 'Пусто' and (
        user_fields.append(existing_user.description))
    user_fields.append(existing_user.field_not_filled)
    return user_fields


# Функция формирования списка и клавиатуры вперед/назад
async def processing_user_list(
    state: FSMContext,
    session: AsyncSession,
    callback_query: CallbackQuery,
    list_counter: int
):
    get_data = await state.get_data()
    users_list, count = await get_user_list(
        session,
        level_id=get_data['level_id'],
        offset=get_data['offset'],
        limit=get_data['limit'],
        role=get_data['role'],
    )
    builder = InlineKeyboardBuilder()
    for user in users_list:
        await get_card_button(user, builder)
    builder.adjust(1)
    await callback_query.message.answer(
        Messages.LIST_OUTPUT,
        reply_markup=builder.as_markup(resize_keyboard=True)
    )
    if count == 0:
        keyboard = await get_buttons(back=Buttons.BACK)
        await state.update_data(offset=START_OFFSET)
        return await callback_query.message.answer(
            Messages.NOTHING_WAS_FIND,
            reply_markup=keyboard
        )
    elif count < get_data['limit']:
        keyboard = await get_buttons(to_begin=Buttons.TO_BEGIN)
        await state.update_data(offset=START_OFFSET)
        return await callback_query.message.answer(
            Messages.LOOK_OR_BACK,
            reply_markup=keyboard
        )
    else:
        if get_data['offset'] == 0:
            if (
                count == int(get_data['limit'])
            ):
                keyboard = await get_buttons(
                    to_begin=Buttons.TO_BEGIN
                )
            else:
                next_start_pag = (
                    int(get_data['offset']) + int(get_data['limit']) + 1
                )
                keyboard = await get_buttons(
                    to_begin=Buttons.TO_BEGIN,
                    next=Buttons.NEXT.format(
                        next_start_pag,
                        count
                    )
                )
        else:
            if int(get_data['offset']) + int(get_data['limit']) < count:
                next_start_pag = (
                    int(get_data['offset']) + int(get_data['limit']) + 1
                )
                previous_end_pag = int(get_data['offset'])
                keyboard = await get_buttons(
                    back=Buttons.BACK.format(
                        1,
                        previous_end_pag
                    ),
                    next=Buttons.NEXT.format(
                        next_start_pag,
                        count
                    ),
                    to_begin=Buttons.TO_BEGIN
                )
            else:
                previous_end_pag = int(get_data['offset'])
                keyboard = await get_buttons(
                    back=Buttons.BACK.format(
                        1,
                        previous_end_pag
                    ),
                    to_begin=Buttons.TO_BEGIN
                )
        if count % int(get_data['limit']) != 0:
            all_list_count = count // int(get_data['limit']) + 1
        else:
            all_list_count = count // int(get_data['limit'])
        await state.update_data(offset=get_data['offset'] + len(users_list))
        list_counter += 1
        await state.update_data(list_counter=list_counter)
        return await callback_query.message.answer(
            Messages.LOOK_OR_NEXT_OR_BACK.format(
                list_counter,
                all_list_count
            ),
            reply_markup=keyboard
        )
