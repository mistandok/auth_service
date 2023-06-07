"""Модуль содержит декораторы для работы с пользователями."""
from functools import wraps
from http import HTTPStatus
from flask_jwt_extended import get_jwt

from core.config import DB_SETTINGS
from services.http_exceptions.auth_exceptions import PermissionDenied
from services.user.utils import is_admin_user
from services.logs import logs

logger = logs.get_logger()


def admin_required(func):
    """
    Декоратор, осуществляющий проверку пользователя
    на наличие прав администратора.
    """
    wraps(func)

    def wrapper(*args, **kwargs):
        access_token = get_jwt()
        user_id = access_token.get('sub').get('user_id')
        user_role = access_token.get('sub').get('user_roles')

        if DB_SETTINGS.admin not in user_role:
            logger.warning(
                'Пользователь %s попытался получить доступ к объекту %s',
                user_id,
                func.__name__,
            )
            raise PermissionDenied(
                'С текущими правами доступ запрещен',
                HTTPStatus.FORBIDDEN,
            )

        return func(*args, **kwargs)

    return wrapper
