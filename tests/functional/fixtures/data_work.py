"""Модуль содержит в себе фикстуры для работы с тестовыми данными."""

import pytest_asyncio
from aioredis import Redis
from aiohttp.client import ClientSession
from asyncpg.connection import Connection as pg_connection

from tests.functional.utils.data_work import cleanup_cache_storage, cleanup_sql_storage
from tests.functional.utils.data_work import user_login, signup_user
from tests.functional.settings import DB_SETTINGS


@pytest_asyncio.fixture(scope='session', autouse=True)
async def data_work(
        redis_blocklist_client: Redis,
        redis_refresh_list_client: Redis,
        db_connection: pg_connection
):
    """
    Фикстура отвечает за работу с данными в хранилищах
    в начале сессиии и перед завершением сессии.
    Перед завершением сессии происходит
    удаление тестовых данных и кэша из используемых хранилищ.
    """
    yield
    await cleanup_sql_storage(db_connection)
    await cleanup_cache_storage(redis_blocklist_client)
    await cleanup_cache_storage(redis_refresh_list_client)


@pytest_asyncio.fixture(scope='session', autouse=True)
async def prepare_tokens(
    api_session: ClientSession
):
    """
    Фикстура отвечает за подготовительные дейсвия
    и их завершение, при необходимости.
    """
    admin_access_token, admin_refresh_token = await user_login(api_session, DB_SETTINGS.admin, DB_SETTINGS.admin)
    test_login = 'test_user'
    test_email = 'test_email'
    test_pwd = 'test_pwd'
    await signup_user(api_session, test_login, test_email, test_pwd)
    test_access_token, test_refresh_token = await user_login(api_session, test_login, test_pwd)
    yield {
        DB_SETTINGS.admin: {
            'access_token': admin_access_token,
            'refresh_token': admin_refresh_token
        },
        'test_user': {
            'access_token': test_access_token,
            'refresh_token': test_refresh_token
        }
    }

