"""Модуль содержит исключения связанные с аутентификацией."""
from .base import HTTPException


class IncorrectPassword(HTTPException):
    """Некорректный пароль."""


class EmptyUserLoginHistory(HTTPException):
    """Пустая история входа в аккаунт пользователя."""


class PermissionDenied(HTTPException):
    """Доступ запрещен"""
