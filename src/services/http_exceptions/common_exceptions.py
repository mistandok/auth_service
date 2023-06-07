"""Модуль содержит исключения связанные с общими вещами."""
from .base import HTTPException


class MissingUpdatedData(HTTPException):
    """Отсутствуют данные для обновления."""


class MissingEntity(HTTPException):
    """Отсутствует какая-либо сущность."""


class InvalidData(HTTPException):
    """Переданы некорректные данные."""


class DuplicatedEntity(HTTPException):
    """Такая сущность уже существует."""


class HTTPIntegrityError(HTTPException):
    """Возник конфликт при интеграции."""


class TooManyRequests(HTTPException):
    """Слишком много запросов."""


class TokenExpired(HTTPException):
    """Срок действия токена истёк."""


class MissingRealization(Exception):
    """Отсутствует интерфейс."""


class MissingSearchData(HTTPException):
    """Отсутствуют данные для поиска."""
