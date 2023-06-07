"""модуль содержит декораторы для помощи в работе с исключениями."""
from functools import wraps

from .base import HTTPException
from services.logs import logs

logger = logs.get_logger()


def http_exceptions_handler(tracked_exceptions: tuple[type(HTTPException)] = (HTTPException,)):
    """
    Декоратор отлавливает ожидаемые HTTP-исключения исключения и возвращает их в виде HTTP-ответа, понятного клиенту.

    Args:
        tracked_exceptions: отслеживаемые исключения.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            try:
                return func(*args, **kwargs)
            except tuple(tracked_exceptions) as error:
                return error.response()

        return wrapper

    return decorator
