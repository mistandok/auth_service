"""Модуль содержит различные утилиты для работы с пользователями."""

import secrets
import uuid
from collections import defaultdict
from http import HTTPStatus
from operator import le, ge
from string import ascii_letters

from sqlalchemy import insert, delete, select, and_, asc, Select, Result
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.query import Query

from core.config import DB_SETTINGS
from db import db_session
from db_models import User, user_role, OAuthUser, Role
from schemes import users_schema
from services.http_exceptions.common_exceptions import HTTPIntegrityError, MissingEntity, MissingSearchData
from services.logs import logs
from services.oauth.parsers import OAuthUserInfo
from services.role.utils import get_user_roles, get_roles_by_names
from services.utils import SearchInfoUserParams

logger = logs.get_logger()


def is_user_exists(email: str, login: str) -> tuple[bool, bool]:
    """
    Функция проверяет существует ли пользователь с заданным логином или емэйлом.

    Args:
        email: email пользователя.
        login: login пользователя.
    Returns:
        tuple[bool, bool]: tuple[0] - существует с таким же email, tuple[1] - существует с таким же login
    """
    column_email = db_session.query(User.id).filter(User.email == email).label('email_id')
    column_login = db_session.query(User.id).filter(User.login == login).label('login_id')

    result = list(db_session.execute(db_session.query(column_email, column_login)))[0]

    return (
        bool(result.email_id),
        bool(result.login_id),
    )


def create_user(user: User):
    """
    Метод создает пользователя без подтверждения транзакции сессии.

    Args:
        user: модель пользователя.
    """
    db_session.add(user)


def get_user_by_id(user_id: uuid) -> Query | None:
    """
    Поиск пользователя по ID.

    Args:
        user_id: ID пользователя

    Returns:
        Query: sqlalchemy.orm запрос
    """
    return db_session.query(User).where(User.id == user_id).first()


def get_user_by_email(email: str) -> Query | None:
    """
    Поиск пользователя по email.

    Args:
        email: email пользователя

    Returns:
        Query: sqlalchemy.orm запрос
    """
    return db_session.query(User).where(User.email == email).first()


def get_user_by_login(login: str) -> User | None:
    """
    Поиск пользователя по login.

    Args:
        login: login пользователя

    Returns:
        Query: sqlalchemy.orm запрос
    """
    return db_session.query(User).where(User.login == login).first()


def is_admin_user(user_id: uuid.UUID) -> bool:
    """
    Проверка пользователя по его `id` на наличие прав администратораа.

    Args:
        user_id

    Returns:
        bool
    """
    roles = get_user_roles(user_id)
    roles_name = set(role.get('name') for role in roles)
    return True if DB_SETTINGS.admin in roles_name else False


def update_user(user_id: int, new_values: dict) -> User:
    """
    Функция осуществляет обновление конкретного пользователя.

    Args:
        user_id: ID пользователя.
        new_values: словарь с новыми значениями.

    Returns:
        User
    """
    db_session.query(User).filter_by(id=user_id).update(new_values)


def add_roles_to_user(user_id, role_names: list[str]):
    """
    Функция добавляет указанному пользователю роли.

    Args:
        user_id: ID пользователя.
        role_names: наименования ролей.
    """
    logger.info('Добавляем пользователю user_id: %s роли %s', user_id, role_names)

    roles = get_roles_by_names(role_names)

    if not roles:
        raise MissingEntity(
            msg='В системе нет указанных ролей.',
            http_status=HTTPStatus.BAD_REQUEST,
        )

    role_ids = [role.get('id') for role in roles]
    values_for_insert = list({'user_id': user_id, 'role_id': role_id} for role_id in role_ids)

    try:
        db_session.execute(
            insert(user_role)
            .values(values_for_insert)
        )
    except IntegrityError:
        logger.warning(
            'Попытка добавить пользователю user_id: %s, новые роли: %s',
            user_id,
            role_ids,
            exc_info=True,
        )
        raise HTTPIntegrityError(
            msg='Конфликт при создании ролей пользователя.',
            http_status=HTTPStatus.CONFLICT,
        )


def delete_roles_from_user(user_id, role_names: list[str]):
    """
    Функция удаляет у указанного пользователя роли.

    Args:
        user_id: ID пользователя.
        role_names: наименования ролей.
    """
    logger.info('Удаляем у пользователя user_id: %s роли %s', user_id, role_names)

    roles = get_roles_by_names(role_names)

    if not roles:
        raise MissingEntity(
            msg='В системе нет указанных ролей.',
            http_status=HTTPStatus.BAD_REQUEST,
        )

    role_ids = [role.get('id') for role in roles]

    try:
        db_session.execute(
            delete(user_role)
            .where(and_(user_role.columns.user_id == user_id, user_role.columns.role_id.in_(role_ids)))
            .returning(user_role.columns.role_id)
        ).scalars().all()
    except IntegrityError:
        logger.warning(
            'Попытка удалить у пользователя user_id: %s, роли: %s',
            user_id,
            role_ids,
            exc_info=True,
        )
        raise HTTPIntegrityError(
            msg='Конфликт при удалении ролей пользователя.',
            http_status=HTTPStatus.CONFLICT,
        )


def generate_random_string(count_letters: int) -> str:
    """Метод создаёт набор данных для записи в таблицу `user`"""
    return ''.join(secrets.choice(ascii_letters) for _ in range(count_letters))


def generate_email(count_letters: int) -> str:
    """Метод создаёт набор данных для записи в таблицу `user`"""
    email = ''.join(secrets.choice(ascii_letters) for _ in range(count_letters)) + "@auth.com"
    return email


def create_user_by_oauth_user_info(user_info: OAuthUserInfo) -> User:
    """
    Метод создаёт пользователя в БД `user` по данным, полученные при OAuth аутентификации

    Args:
        user_info: dataclass со спарсенной информацией

    Returns:
        объект User
    """
    login = generate_random_string(8)
    password = generate_random_string(8)
    email = user_info.email or generate_email(8)

    user = User(login=login, password=password, email=email)
    db_session.add(user)
    db_session.flush()

    return user


def create_oauth_user(user_info: dict) -> None:
    """
    Метод создаёт запись в БД `OAuthUser` по данный из `user_info`

    Args:
        user_info: словарь с необходимыми полями
    """

    query = OAuthUser.insert().values(**user_info)
    db_session.execute(query)


class InfoUsersList:
    """Класс предоставляющий доступ к персональной информации о пользователях в списковом формате."""

    def __init__(self, params: dict):
        self.params = params
        print(params)
        self._limit = self.params.get(SearchInfoUserParams.LIMIT.value)
        self._page_number = self.params.get(SearchInfoUserParams.PAGE_NUMBER.value)
        self._answer_body = defaultdict(list)

    def get(self) -> dict:
        """
        Метод получает персональную информацию о пользователях.

        Returns:
            Словарь с информацией о пользователях
        """

        query_by_func = self._get_query()

        result = db_session.execute(query_by_func)
        self._build_page_answer(result)

        return self._answer_body

    def _get_query(self) -> Select | str:
        """
        Метод формирует запрос в зависимости от параметра поиска или выдаёт ошибку

        Returns:
            Сортированный SQL-запрос или ошибку
        """
        if self.params.get(SearchInfoUserParams.USER_IDS.value):
            query = self._user_model_query(self.params.get(SearchInfoUserParams.USER_IDS.value))
        elif self.params.get(SearchInfoUserParams.USER_GROUPS.value):
            query = self._user_role_model_query(self.params.get(SearchInfoUserParams.USER_GROUPS.value))
        else:
            query = select(User)
        return (
            query
            .order_by(asc(User.created_at))
            .limit(self._limit + 1)
            .offset((self._page_number - 1) * self._limit)
        )

    def _user_model_query(self, user_ids: list) -> Select:
        """
        Метод формирует запрос в SQL-запрос для получения пользователей по `id` из `user_ids`

        Args:
            user_ids: список UUID пользователей

        Returns:
            Select query
        """

        query = (
            select(User)
            .where(User.id.in_(user_ids))
        )
        return query

    def _user_role_model_query(self, role_names: list[str]) -> Select:
        """
        Метод формирует запрос в SQL-запрос для получения пользователей соотв. группы из `role_names`

        Args:
            role_names: список названий групп

        Returns:
            Select query
        """
        query = (
            select(User)
            .join(user_role)
            .join(Role)
            .where(Role.name.in_(role_names))
        )
        return query

    def _build_page_answer(self, result: Result) -> None:
        """
        Метод формирует страницу ответа по персональной инфо о пользователях

        Args:
            result: SQLAlchemy запрос
        """

        info_users = list(result.scalars())
        length = len(info_users)
        serialize = users_schema.dump

        if length > self._limit:
            obj, next_page = serialize(info_users[:self._limit]), self._page_number + 1
        else:
            obj, next_page = serialize(info_users[:length]), None

        self._answer_body['result'] = obj
        self._answer_body['outcome'].append({'next_page': next_page})
