import re

from sqlalchemy.ext.asyncio import AsyncSession

from .base import validate_existence, validate_length, validate_pattern
from .constants import (ValidatorsIntValues, ValidatorsMessages,
                        ValidatorsStrValues)


async def validate_school21_nickname(
        school21_nickname: str,
        session: AsyncSession
):
    # Проверка длины никнейма
    length_error = await validate_length(
        school21_nickname,
        ValidatorsIntValues.SCHOOL21NICKNAME_MIN_LEN,
        ValidatorsIntValues.SCHOOL21NICKNAME_MAX_LEN,
        ValidatorsMessages.SCHOOL21NICKNAME_LEN_ERROR
    )
    if length_error:
        return length_error

    # Проверка на латиницу
    pattern_error = await validate_pattern(
        school21_nickname,
        ValidatorsStrValues.LATIN_ONLY_PATTERN,
        ValidatorsMessages.LATIN_ERROR
    )
    if pattern_error:
        return pattern_error

    # Проверка на существование никнейма в базе данных
    existence_error = await validate_existence(
        school21_nickname,
        session,
        ValidatorsMessages.SCHOOL21NICKNAME_EXIST_ERROR,
        'school21_nickname'
    )
    if existence_error:
        return existence_error

    return None


async def validate_sber_id(
        sber_id: str,
        session: AsyncSession
):
    # Проверка длины sber_id
    length_error = await validate_length(
        sber_id,
        ValidatorsIntValues.ALL_MIN_LEN,
        ValidatorsIntValues.SBER_ID_TEAM_NAME_MAX_LEN,
        ValidatorsMessages.SBER_ID_LEN_ERROR
    )
    if length_error:
        return length_error

    # Проверка на SberID паттерн
    pattern_error = await validate_pattern(
        sber_id,
        ValidatorsStrValues.SBER_ID_PATTERN,
        ValidatorsMessages.SBER_ID_ERROR
    )
    if pattern_error:
        return pattern_error

    return None


async def validate_team_name(
    team_name: str,
    session: AsyncSession,
):
    # Проверка длины названия команды
    length_error = await validate_length(
        team_name,
        ValidatorsIntValues.ALL_MIN_LEN,
        ValidatorsIntValues.SBER_ID_TEAM_NAME_MAX_LEN,
        ValidatorsMessages.TEAM_NAME_LEN_ERROR
    )
    if length_error:
        return length_error

    return None


async def validate_description(
    description: str,
    session: AsyncSession
):
    # Проверка длины описания
    length_error = await validate_length(
        description,
        ValidatorsIntValues.ALL_MIN_LEN,
        ValidatorsIntValues.DESCRIPTION_MAX_LEN,
        ValidatorsMessages.DESCRIPTION_LEN_ERROR
    )
    if length_error:
        return length_error

    return None


async def validate_role_level(
        role_level: str,
        session: AsyncSession
):
    # Проверка на паттерн
    pattern_error = await validate_pattern(
        role_level,
        ValidatorsStrValues.ROLE_PATTERN,
        ValidatorsMessages.ROLE_ERROR
    )

    if pattern_error:
        return pattern_error

    # Проверка на корректность ввода уровня
    match = re.match(ValidatorsStrValues.ROLE_PATTERN, role_level)

    if (match is None or
            (match.group(1) in ValidatorsStrValues.ROLE_LEVELS and
             not match.group(2))):
        return ValidatorsMessages.ROLE_ERROR

    return None
