"""Модуль содержит различные утилиты для работы с разрешениями пользователей."""

from uuid import UUID
from http import HTTPStatus

from sqlalchemy import select, and_

from db import db_session
from services.permissions.config import AccessLevel, RoleName, ScopeName
from services.http_exceptions.common_exceptions import InvalidData
from db_models import Permissions, Scope, user_role, Role


def get_access_level(
    add_admin: bool = False,
    add_write: bool = False,
    add_read: bool = False
) -> int:
    """Функция формирует права по параметрам."""

    return (
        (AccessLevel.ADMIN if add_admin else 0) +
        (AccessLevel.WRITE if add_write else 0) +
        (AccessLevel.READ if add_read else 0)
    )


def calculate_permissions(access_level: int) -> dict:
    """Функция выполняет рассчёт разрешений по уровню доступа пользователя."""

    return {
        'admin': bool(access_level & AccessLevel.ADMIN),
        'write': bool(access_level & AccessLevel.WRITE),
        'read': bool(access_level & AccessLevel.READ)
    }


def get_user_permissions_by_scope(scope_name: str, user_id: UUID | None) -> dict:
    """
    Функция выполняет запрос в БД по параметрам `scope` и `user_id`
    и возвращает уровень всех разрешений пользователя по всем имеющимся у него ролям.
    При отсутствии `user_id` функция выполняет запрос по `scope` и роли `incognito`.
    """

    if scope_name not in [s_name.value for s_name in ScopeName]:
        raise InvalidData('Передано некорректное имя области разрешения.', HTTPStatus.BAD_REQUEST)

    if user_id:
        query = (
            select(Permissions.access_level).
            outerjoin(Scope, Permissions.scope_id == Scope.id).
            outerjoin(user_role, Permissions.role_id == user_role.columns.role_id).
            where(and_(Scope.name == scope_name, user_role.columns.user_id == user_id))
        )
        user_access_levels = tuple(db_session.execute(query).scalars())
        result = 0
        for access_level in user_access_levels:
            result = result | access_level

    else:
        query = (
            select(Permissions.access_level).
            outerjoin(Role, Permissions.role_id == Role.id).
            outerjoin(Scope, Permissions.scope_id == Scope.id).
            where(and_(Scope.name == scope_name, Role.name == RoleName.INCOGNITO.value))
        )
        result = db_session.execute(query).scalar()

    permissions = calculate_permissions(result)

    return permissions
