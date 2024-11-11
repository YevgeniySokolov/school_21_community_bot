import logging
import os
from datetime import datetime

from aiogram import F
from aiogram.dispatcher.router import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (CallbackQuery, ContentType, FSInputFile, Message,
                           ReplyKeyboardRemove)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.bot import TELEGRAM_TOKEN
from bot.decorators import admin_required, db_session_decorator, private_only
from bot.keyboards.keyboards import get_admin_buttons
from bot.messages import Admin_messages, Messages
from bot.states.states import Admin_state, FixtureImportState, Start_state
from bot.utils import (create_orm_dump, download_file, find_duplicates,
                       load_existing_data, load_json_data, xor_encr_decr)
from database.models import AdminSettings, Level, User, moscow_tz
from logger.logmessages import LogMessage
from settings import DATE_FORMAT, DUMP_FILE_NAME

router = Router()
hndlr_logger = logging.getLogger('HNDLR_LOGGER')


# Обработчик для кнопки "Панель администратора"
@router.message(
    StateFilter(Start_state.wait_for_action),
    F.text == "Панель администратора"
)
@private_only
async def role_selection_keyb(message: Message, state: FSMContext):
    await message.answer(
        Admin_messages.LIST_COMMANDS,
        reply_markup=ReplyKeyboardRemove()
    )
    keyboard = await get_admin_buttons()
    await message.answer(
        Admin_messages.LIST_DESCRIPTION,
        reply_markup=keyboard
    )
    await state.set_state(Admin_state.waiting_for_commands)


@router.callback_query(
    StateFilter(Admin_state.waiting_for_commands),
    F.data.contains("crypt_base")
)
@db_session_decorator
@admin_required
@private_only
async def encrypt_decrypt_base_handler(
    callback_query: CallbackQuery,
    session: AsyncSession
):
    hndlr_logger.info(
        LogMessage.CRYPT_BASE_REQUEST.format(callback_query.from_user.id)
    )
    # Получаем всех пользователей из базы данных
    users = await session.execute(select(User))
    users = users.scalars().all()

    admin_settings = await session.execute(select(AdminSettings).limit(1))
    admin_settings = admin_settings.scalar()

    operation = (
        "ЗАШИФРОВАНА" if not admin_settings.is_encrypted else "ДЕШИФРОВАНА"
    )

    for user in users:
        # Обновляем зашифрованные значения в объекте user
        user.username = xor_encr_decr(
            user.username, TELEGRAM_TOKEN
        )
        user.sber_id = xor_encr_decr(
            user.sber_id, TELEGRAM_TOKEN
        )
        user.role = xor_encr_decr(
            user.role, TELEGRAM_TOKEN
        )
        user.team_name = xor_encr_decr(
            user.team_name, TELEGRAM_TOKEN
        )
        user.description = xor_encr_decr(
            user.description, TELEGRAM_TOKEN
        )
        user.school21_nickname = xor_encr_decr(
            user.school21_nickname, TELEGRAM_TOKEN
        )

    # Шифруем данные уровней
    levels = await session.execute(select(Level))
    levels = levels.scalars().all()

    for level in levels:
        # Обновляем зашифрованное значение в объекте level
        level.name = xor_encr_decr(level.name, TELEGRAM_TOKEN)

    # признак шифровки=1/дешифровки=0
    admin_settings.is_encrypted = not admin_settings.is_encrypted
    # кем произведено действие
    admin_settings.updated_by = callback_query.from_user.id
    # когда произведено действие
    admin_settings.last_updated = datetime.now(moscow_tz)

    # Сохраняем изменения в базе данных
    await session.commit()
    hndlr_logger.info(LogMessage.JOB_IS_DONE)

    # Отправляем сообщение пользователю, что процесс завершен
    keyboard = await get_admin_buttons()
    await callback_query.message.answer(
        Messages.DATA_BASE_CRYPTED_MESSAGE.format(operation=operation),
        reply_markup=keyboard
    )
    callback_query.answer()


@router.callback_query(
    StateFilter(Admin_state.waiting_for_commands),
    F.data.contains("fixtures_export")
)
@db_session_decorator
@admin_required
@private_only
async def send_dump(
    callback_query: CallbackQuery,
    session: AsyncSession
):
    hndlr_logger.info(
        LogMessage.DUMP_BASE_REQUEST.format(callback_query.from_user.id)
    )
    dump_file_path = DUMP_FILE_NAME
    # Создаем дамп базы данных
    await create_orm_dump(session, dump_file_path)

    # Открываем JSON файл для отправки
    dump_file = FSInputFile(dump_file_path)

    # Отправляем файл пользователю
    keyboard = await get_admin_buttons()
    await callback_query.message.answer(Messages.DATA_SUCCESS_UPLOAD)
    await callback_query.message.answer_document(dump_file)
    await callback_query.message.answer(
        Messages.OPERATION_SUCCESS,
        reply_markup=keyboard
    )
    hndlr_logger.info(LogMessage.JOB_IS_DONE)
    # Удаляем файл после отправки
    os.remove(dump_file_path)


@router.callback_query(
    StateFilter(Admin_state.waiting_for_commands),
    F.data.contains("fixtures_import")
)
@db_session_decorator
@admin_required
@private_only
async def request_fixtures_file(
    callback_query: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    await callback_query.message.answer(
        Messages.SEND_JSON_FILE_MESSAGES
    )
    # Устанавливаем состояние ожидания загрузки файла
    await state.set_state(FixtureImportState.waiting_for_file)
    await callback_query.answer()


@router.message(
    FixtureImportState.waiting_for_file,
    F.content_type == ContentType.DOCUMENT
)
@db_session_decorator
@admin_required
@private_only
async def handle_fixtures_file(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    if not (file_path := await download_file(message)):
        return

    data = await load_json_data(file_path)

    # Проверка формата файла
    if any(key not in data for key in ["users", "levels"]):
        await message.answer(Messages.ERROR_FILE_FORMAT)
        os.remove(file_path)

    # Загрузка существующих данных из базы
    existing_users, existing_levels = await load_existing_data(session)

    fields_to_check = (
        "id", "telegram_id", "username", "sber_id", "school21_nickname",
    )
    duplicate_messages = []

    for field in fields_to_check:
        duplicates = find_duplicates(data, field)
        if duplicates:
            duplicates_str = ', '.join(map(str, duplicates))
            duplicate_messages.append(f"{field}: {duplicates_str}")

    if duplicate_messages:
        await message.answer(
            Messages.ERROR_FIXTURE_FILE_DUBLICATES.format(
                dublicates="; ".join(duplicate_messages)
            )
        )
        os.remove(file_path)
        return

    # Проверка и обработка пользователей
    for user_data in data["users"]:
        db_user = existing_users.get(user_data["telegram_id"])

        # Обновляем данные существующего пользователя или добавляем нового
        if "registration_date" in user_data and isinstance(
            user_data["registration_date"], str
        ):
            user_data["registration_date"] = datetime.strptime(
                user_data["registration_date"], DATE_FORMAT
            )

        if db_user:
            for field in user_data:
                if hasattr(db_user, field):
                    setattr(db_user, field, user_data[field])
                else:
                    await message.answer(
                        Messages.ERROR_FIELD_FIXTURE_USER.format(field=field)
                    )
                    os.remove(file_path)
                    return
        else:
            new_user = User(**user_data)
            session.add(new_user)

    # Проверка и обработка уровней
    for level_data in data["levels"]:
        db_level = existing_levels.get(level_data["id"])
        # Обновляем данные существующего уровня или добавляем новый
        if db_level:
            for field in level_data:
                if hasattr(db_level, field):
                    setattr(db_level, field, level_data[field])
                else:
                    await message.answer(
                        Messages.ERROR_FIELD_FIXTURE_LEVEL.format(field=field)
                    )
                    os.remove(file_path)
                    return
        else:
            new_level = Level(**level_data)
            session.add(new_level)

    # Коммит изменений и отправка ответа
    await session.commit()
    keyboard = await get_admin_buttons()
    await message.answer(
        Messages.DATA_SUCCESS_LOADED,
        reply_markup=keyboard
    )
    # Удаление временного файла
    os.remove(file_path)
    # Очистка состояния
    await state.clear()
