"""Модуль с созданием админа и его прав."""
from enum import Enum
from functools import lru_cache, wraps
from http import HTTPStatus
from typing import Callable, Generator
from uuid import uuid4

from sqlalchemy import select, insert
from sqlalchemy.exc import IntegrityError, InternalError
from sqlalchemy.ext.declarative import declarative_base

from core.config import DB_SETTINGS, APP_SETTINGS
from db import db_session
from db_models import User, Role, user_role, Scope, Permissions
from schemes import base_schema
from services.passwords.utils import get_hash_password
from services.permissions.config import ScopeName, RoleName
from services.permissions.utils import get_access_level


@lru_cache
def is_admin_exist(func):
    """Функция проверят наличие админа в базе."""

    def wrapper():
        query = select(
            User
        ).where(
            User.login == DB_SETTINGS.admin
        )
        result = db_session.execute(query)

        if result.scalar():
            return
        return func()

    return wrapper


@is_admin_exist
def create_admin_user():
    """Функция создаёт пользователя с правами админа."""

    admin_user = {
        'id': uuid4(),
        'login': DB_SETTINGS.admin,
        'first_name': DB_SETTINGS.admin,
        'surname': DB_SETTINGS.admin,
        'patronymic': DB_SETTINGS.admin,
        'email': DB_SETTINGS.admin,
        'password': get_hash_password(DB_SETTINGS.admin)
    }

    role_admin = {
        'id': uuid4(),
        'name': DB_SETTINGS.admin,
        'description': 'superuser'
    }

    for model, datas in zip([User, Role], [admin_user, role_admin]):
        data = model(**datas)
        db_session.add(data)
        db_session.commit()

    relation = user_role.insert().values(
        user_id=admin_user.get('id'),
        role_id=role_admin.get('id')
    )

    db_session.execute(relation)
    db_session.commit()


def create_scopes():
    """Функция создаёт записи имён областей разрешений в БД."""

    scope_names = {scope_name.value for scope_name in ScopeName}

    db_scope_names = tuple(db_session.execute(select(Scope.name)).scalars())
    for scope_name in db_scope_names:
        scope_names.discard(scope_name)
    if scope_names:
        scope_names = [{'name': scope_name} for scope_name in scope_names]
        _insert_values(Scope, scope_names)


def create_roles():
    """Функция создаёт записи ролей в БД, кроме админской."""

    role_names = {role_name.value for role_name in RoleName if role_name.value != RoleName.ADMIN.value}

    db_role_names = tuple(db_session.execute(select(Role.name)).scalars())
    for role_name in db_role_names:
        role_names.discard(role_name)
    if role_names:
        role_names = [{'name': role_name, 'description': f'{role_name} role'} for role_name in role_names]
        _insert_values(Role, role_names)


def create_permissions():
    """Функция, создающая записи разрешений в БД."""

    def _generate_permissions_list():
        """Вспомогательная функция, для преобразования значений."""

        scope_id_acc_lvl_dict = {
            scopes.get(scope_name): access_levels.get(scope_name) for scope_name in access_levels
        }
        permissions = [
            {
                'role_id': role_id,
                'scope_id': scope_id,
                'access_level': acc_lvl
            } for scope_id, acc_lvl in scope_id_acc_lvl_dict.items()
        ]
        return permissions

    roles = dict(db_session.execute(select(Role.name, Role.id)).all())
    scopes = dict(db_session.execute(select(Scope.name, Scope.id)).all())

    all_permissions = []

    for role_name, role_id in roles.items():

        if role_name == RoleName.ADMIN.value:
            access_levels = {
                ScopeName.FILMS.value:         get_access_level(add_admin=True, add_write=True, add_read=True),
                ScopeName.FILM_DETAIL.value:   get_access_level(add_admin=True, add_write=True, add_read=True),
                ScopeName.PERSONS.value:       get_access_level(add_admin=True, add_write=True, add_read=True),
                ScopeName.PERSON_DETAIL.value: get_access_level(add_admin=True, add_write=True, add_read=True),
                ScopeName.GENRES.value:        get_access_level(add_admin=True, add_write=True, add_read=True),
                ScopeName.PROTECTED.value:     get_access_level(add_admin=True, add_write=True, add_read=True)
            }
            permissions = _generate_permissions_list()

        elif role_name == RoleName.SUBSCRIBER.value:
            access_levels = {
                ScopeName.FILMS.value:         get_access_level(add_read=True),
                ScopeName.FILM_DETAIL.value:   get_access_level(add_read=True),
                ScopeName.PERSONS.value:       get_access_level(add_read=True),
                ScopeName.PERSON_DETAIL.value: get_access_level(add_read=True),
                ScopeName.GENRES.value:        get_access_level(add_read=True),
                ScopeName.PROTECTED.value:     get_access_level()
            }
            permissions = _generate_permissions_list()

        elif role_name == RoleName.USER.value:
            access_levels = {
                ScopeName.FILMS.value:         get_access_level(add_read=True),
                ScopeName.FILM_DETAIL.value:   get_access_level(),
                ScopeName.PERSONS.value:       get_access_level(add_read=True),
                ScopeName.PERSON_DETAIL.value: get_access_level(),
                ScopeName.GENRES.value:        get_access_level(add_read=True),
                ScopeName.PROTECTED.value:     get_access_level()
            }
            permissions = _generate_permissions_list()

        elif role_name == RoleName.INCOGNITO.value:
            access_levels = {
                ScopeName.FILMS.value:         get_access_level(add_read=True),
                ScopeName.FILM_DETAIL.value:   get_access_level(),
                ScopeName.PERSONS.value:       get_access_level(),
                ScopeName.PERSON_DETAIL.value: get_access_level(),
                ScopeName.GENRES.value:        get_access_level(),
                ScopeName.PROTECTED.value:     get_access_level()
            }
            permissions = _generate_permissions_list()

        all_permissions.extend(permissions)

    for permission in all_permissions:
        _insert_values(Permissions, permission)


def fallback_exception_response(*args, **kwargs) -> tuple[base_schema, HTTPStatus]:
    """Базовый ответ в случае неожиданной ошибки в функции."""
    return (
        base_schema.dump(dict(msg='Что-то полшло не так, мы уже работаем над решением проблемы')),
        HTTPStatus.INTERNAL_SERVER_ERROR,
    )


def _insert_values(table_model: declarative_base, values: list[dict]):
    """Функция, записывающая данные в БД."""

    try:
        db_session.execute(insert(table_model).values(values))
        db_session.commit()
    except IntegrityError:
        pass
    except InternalError:
        db_session.rollback()
        try:
            db_session.execute(insert(table_model).values(values))
            db_session.commit()
        except IntegrityError:
            pass


def coroutine(foo: Callable):
    """Метод инициализирует генератор"""
    @wraps(foo)
    def wrapper(*args, **kwargs) -> Generator:
        generator = foo(*args, **kwargs)
        generator.send(None)
        return generator
    return wrapper


def exclude_for_test(foo):
    """Метод исключает работу методов при запуске тестирования."""

    @wraps(foo)
    def wrapper(*args, **kwargs):
        if APP_SETTINGS.test.lower() == 'true':
            return
        return foo(*args, **kwargs)

    return wrapper


class SearchInfoUserParams(str, Enum):
    """Класс наименований параметров поиска"""

    USER_IDS = "user_ids"
    USER_GROUPS = "user_groups"
    PAGE_NUMBER = "page_number"
    LIMIT = 'limit'


if __name__ == '__main__':
    create_admin_user()
    create_roles()
    create_scopes()
    create_permissions()
