"""Модуль содержит в себе функции, реализующие работу с тестовыми данными."""

from aioredis import Redis
from aiohttp.client import ClientSession
from asyncpg.connection import Connection as pg_connection

from tests.functional.utils.api import api_get_request


async def user_login(
        api_session: ClientSession,
        login: str,
        pwd: str
) -> tuple[str, str]:
    """
    Функция реализующая вход в систему пользователя.

    Args:
        api_session: экзепляр клиентской сессии.
        login: логин пользователя.
        pwd: пароль пользователя.

    Returns:
        кортеж токенов.
    """
    query = {
        "login": login,
        "password": pwd
    }
    url = '/auth/api/v1/account/login'
    body, headers, status = await api_get_request(api_session, 'post', url, json=query)
    return body.get('access_token'), body.get('refresh_token')


async def signup_user(
        api_session: ClientSession,
        login: str,
        email: str,
        pwd: str
):
    """
    Функция реализующая регистрацию пользователя.

    Args:
        api_session: экзепляр клиентской сессии.
        login: логин пользователя.
        email: e-mail пользователя.
        pwd: пароль пользователя.
    """
    query = {
        "login": login,
        "email": email,
        "password": pwd
    }
    url = '/auth/api/v1/account/signup'
    await api_get_request(api_session, 'post', url, json=query)


async def cleanup_cache_storage(cache_client: Redis):
    """
    Очистка тестового хранилища кэша один раз по окончанию сессии.

    Args:
        cache_client: экземпляр клиента хранилища кэша.
    """
    await cache_client.flushdb(async_op=True)


async def cleanup_sql_storage(db_connection: pg_connection):
    """
    Очистка тестового хранилища.

    Args:
        db_connection: экземпляр соединения хранилища.
    """

    await db_connection.execute("""
        DELETE FROM auth.user_auth_history;
        DELETE FROM auth.user_role CASCADE
            WHERE user_id != (
                SELECT id FROM auth.user
                    WHERE login = 'admin'
            );
        DELETE FROM auth.user CASCADE
            WHERE login != 'admin';
        DELETE FROM auth.role CASCADE
            WHERE name != 'admin';
    """)
