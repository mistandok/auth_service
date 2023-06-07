"""Модуль содержит различные утилиты для работы с историей пользователей."""
import uuid
from http import HTTPStatus

from user_agents import parse
from sqlalchemy import desc, and_
from sqlalchemy.exc import DataError

from db import db_session
from db_models import User, UserAuthHistory
from schemes import auth_histories_schema, list_response_schema, ListResponseSchema
from services.http_exceptions.navigation_exceptions import WrongSearchAfter


def create_user_history(user: User, user_agent: str = 'unknown'):
    """
    Функция создает историю по пользователю.
    Раздел device_type записывается в зависимости от устройства:
    mobile, pc или other.

    Args:
        user: пользователь
        user_agent: информация об устройсве, с которого пользователь осуществил вход.
    """
    parsed_user_agent = parse(user_agent)

    if parsed_user_agent.is_pc:
        device_type = 'pc'
    elif parsed_user_agent.is_mobile:
        device_type = 'mobile'
    else:
        device_type = 'other'

    history = UserAuthHistory(
        user_id=user.id,
        user_agent=user_agent,
        device_type=device_type
    )
    return db_session.add(history)


def get_user_history_list(
        user_id: uuid,
        limit: int,
        search_after: list | None = None
) -> ListResponseSchema:
    """
    Функция получает историю по пользователю.

    Args:
        user_id: идентификатор пользователя.
        limit: количество возвращаемых записей.

    Returns:
        list[UserAuthHistory]
    """
    result_search_after = None

    if search_after is None:
        history_query = (
            db_session.query(UserAuthHistory).
            filter_by(user_id=user_id).
            order_by(desc(UserAuthHistory.created_at), desc(UserAuthHistory.id)).
            limit(limit)
        )
    else:
        try:
            created_at,  = search_after
        except ValueError:
            raise WrongSearchAfter(
                'Ошибочные значения для фильтра search_after. '
                'Пример корректных значений: '
                'search_after=2023-02-21T19:43:47.030500&search_after=9dc06f01-93cd-4237-a3c1-d9130e720c35',
                HTTPStatus.BAD_REQUEST
            )

        history_query = (
            db_session.query(UserAuthHistory).filter_by(user_id=user_id).
            where(and_(UserAuthHistory.created_at < created_at)).
            order_by(desc(UserAuthHistory.created_at), desc(UserAuthHistory.id)).
            limit(limit)
        )

    try:
        history = auth_histories_schema.dump(history_query)
    except DataError:
        raise WrongSearchAfter('Некорректные параметры запроса', HTTPStatus.BAD_REQUEST)

    if history:
        last_row = history[-1]
        result_search_after = last_row.get('created_at') if len(history) == limit else None

    result = {
        'result': history,
        'outcome': {
            'search_after': result_search_after,
        }
    }

    return list_response_schema.dump(result)
