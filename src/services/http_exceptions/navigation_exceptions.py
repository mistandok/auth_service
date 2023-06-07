"""Модуль содержит исключения связанные с ошибками навигации."""
from .base import HTTPException


class WrongSearchAfter(HTTPException):
    """Дублирующиеся значения аутентификационных данных."""
