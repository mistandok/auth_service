"""Модуль содержит различные утилиты для работы с ролями."""
from http import HTTPStatus
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from db import db_session
from db_models import Role, user_role
from schemes import ListResponseSchema, RoleSchema, list_response_schema, roles_schema
from services.http_exceptions.common_exceptions import MissingUpdatedData, DuplicatedEntity
from services.logs import logs

logger = logs.get_logger()


def get_user_roles(user_id: UUID) -> list[RoleSchema]:
    """
    Поиск всех ролей пользователя по `id`.

    Args:
        user_id: ID пользователя

    Returns:
        Query: sqlalchemy.orm запрос
    """
    return roles_schema.dump(
        db_session
        .query(Role.name, Role.id)
        .join(user_role)
        .filter(user_role.columns.user_id == user_id)
    )


def get_role_by_id(role_id: UUID) -> Role:
    """
    Функция получает роль по Id

    Args:
        role_id: Идентификатор роли

    Returns:
        Role
    """
    return db_session.execute(db_session.query(Role).filter_by(id=role_id)).scalar()


def get_role_by_name(name: str) -> Role:
    """
    Функция получает роль по имени

    Args:
        name: название роли

    Returns:
        Role
    """
    return db_session.execute(db_session.query(Role).filter_by(name=name)).scalar()


def get_roles_by_names(names: list[str]) -> list[RoleSchema]:
    """
    Функция получает список ролей по именам.

    Args:
        names: названия ролей.
    """
    return roles_schema.dump(db_session.query(Role).filter(Role.name.in_(names)))


def create_role(role: Role):
    """
    Функция создает роль.

    Args:
        role: роль
    """
    db_session.add(role)


def update_role(role_id: UUID, new_name: str | None, new_description: str | None) -> bool:
    """
    Функция обновляет роль.

    Args:
        role_id: ID роли для обновления.
        new_name: новое имя роли.
        new_description: новое описание роли.

    Returns:
        bool: True - запись обновлена. False - запись не обновлена.
    """
    if not new_name and not new_description:
        raise MissingUpdatedData('Не переданы данные для обновления', HTTPStatus.BAD_REQUEST)

    new_values = {}
    if new_name:
        new_values['name'] = new_name
    if new_description:
        new_values['description'] = new_description

    try:
        return bool(db_session.query(Role).filter_by(id=role_id).update(new_values))
    except IntegrityError:
        logger.warning(
            'Попытка обновить роль role_id: %s. new_name: %s, new_description: %s',
            role_id,
            new_name,
            new_description,
            exc_info=True,
        )
        raise DuplicatedEntity('Такое имя роли уже используется.', HTTPStatus.BAD_REQUEST)


def delete_role(role_id: UUID) -> bool:
    """
    Функция удаляет роль.

    Args:
        role_id: ID роли для удаления.

    Returns:
        bool: True - роль удалена, False - такой роли не существовало.
    """
    return bool(db_session.query(Role).filter_by(id=role_id).delete())


def get_role_list() -> ListResponseSchema:
    """
    Функция получает список ролей.

    В системе не будет большого списка ролей, поэтому не обязательно как-то ограничивать этот список.

    Returns:
        ListResponseSchema
    """
    return list_response_schema.dump(
        dict(
            result=roles_schema.dump(db_session.query(Role).all()),
            outcome={},
        )
    )
