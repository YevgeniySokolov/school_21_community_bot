import pytest

from .constants import TestStrValues
from bot.utils import xor_encr_decr
from database.models import AdminSettings, User


def encrypt_user_attributes(user):
    """Шифрует данные пользователя с использованием XOR."""
    return {
        'username': xor_encr_decr(
            user.username,
            TestStrValues.TEST_TELEGRAM_TOKEN
        ),
        'sber_id': xor_encr_decr(
            user.sber_id,
            TestStrValues.TEST_TELEGRAM_TOKEN
        ),
        'role': xor_encr_decr(
            user.role,
            TestStrValues.TEST_TELEGRAM_TOKEN
        ),
        'team_name': xor_encr_decr(
            user.team_name,
            TestStrValues.TEST_TELEGRAM_TOKEN
        ),
        'description': xor_encr_decr(
            user.description,
            TestStrValues.TEST_TELEGRAM_TOKEN
        ),
        'school21_nickname': xor_encr_decr(
            user.school21_nickname,
            TestStrValues.TEST_TELEGRAM_TOKEN
        )
    }


def decrypt_user_attributes(encrypted_user):
    """Дешифрует данные пользователя с использованием XOR."""
    return {
        'username': xor_encr_decr(
            encrypted_user['username'],
            TestStrValues.TEST_TELEGRAM_TOKEN
        ),
        'sber_id': xor_encr_decr(
            encrypted_user['sber_id'],
            TestStrValues.TEST_TELEGRAM_TOKEN
        ),
        'role': xor_encr_decr(
            encrypted_user['role'],
            TestStrValues.TEST_TELEGRAM_TOKEN
        ),
        'team_name': xor_encr_decr(
            encrypted_user['team_name'],
            TestStrValues.TEST_TELEGRAM_TOKEN
        ),
        'description': xor_encr_decr(
            encrypted_user['description'],
            TestStrValues.TEST_TELEGRAM_TOKEN
        ),
        'school21_nickname': xor_encr_decr(
            encrypted_user['school21_nickname'],
            TestStrValues.TEST_TELEGRAM_TOKEN
        )
    }


@pytest.mark.asyncio
async def test_xor_encryption_decryption():
    original_user = User(
        id=1,
        username="test_user",
        sber_id="12345",
        role="devops",
        team_name="team_a",
        description="Test user description",
        school21_nickname="nickname"
    )
    # Шифруем данные пользователя
    encrypted_user = encrypt_user_attributes(original_user)
    # Проверяем, что данные зашифрованы
    for attr in encrypted_user:
        assert encrypted_user[attr] != getattr(original_user, attr)
    # Дешифруем данные и проверяем их соответствие
    decrypted_user = decrypt_user_attributes(encrypted_user)
    for attr in decrypted_user:
        assert decrypted_user[attr] == getattr(original_user, attr)
    # Проверяем настройки администратора
    admin_settings = AdminSettings(
        is_encrypted=True,
        updated_by=12345,
        last_updated="2024-11-11T12:00:00Z"
    )
    assert admin_settings.is_encrypted is True
    assert admin_settings.updated_by == 12345
    assert admin_settings.last_updated is not None
