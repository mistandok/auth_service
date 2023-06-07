"""Модуль отвечает за утилиты для работы с паролями."""

import bcrypt


def get_hash_password(password: str) -> str:
    """
    Функция получает закэшированное значение пароля.

    Args:
        password: пароль.

    Returns:
        hash: захэшированный пароль.
    """
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return password_hash.decode('utf-8')


def is_correct_password(password: str, password_hash: str) -> bool:
    """
    Функция проверяет, что строковое представление пароля совпадает с хэшем.

    Args:
        password: пароль
        password_hash: хэш пароля.

    Returns:
        bool: True - пароль корректный, False - пароль не корректный.
    """
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
