"""Модуль содержит в себе фикстуры для установки соединений с различными сервисами."""

import aiohttp
import aioredis
import asyncpg
from asyncpg.exceptions import ConnectionFailureError
import backoff
import pytest_asyncio

from tests.functional.settings import APP_SETTINGS, DB_SETTINGS, DSL


@backoff.on_exception(backoff.expo, aioredis.RedisError)
@pytest_asyncio.fixture(scope='session')
async def redis_blocklist_client():
    """Фикстура устанавливает соединение с редисом на все время активности сессии."""
    client = await aioredis.create_redis_pool(
        (DB_SETTINGS.redis_host, DB_SETTINGS.redis_port),
        minsize=10,
        maxsize=20
    )
    yield client
    client.close()
    await client.wait_closed()


@backoff.on_exception(backoff.expo, aioredis.RedisError)
@pytest_asyncio.fixture(scope='session')
async def redis_refresh_list_client():
    """Фикстура устанавливает соединение с редисом на все время активности сессии."""
    client = await aioredis.create_redis_pool(
        (DB_SETTINGS.refresh_redis_host, DB_SETTINGS.refresh_redis_port),
        minsize=10,
        maxsize=20
    )
    yield client
    client.close()
    await client.wait_closed()


@backoff.on_exception(backoff.expo, ConnectionFailureError)
@pytest_asyncio.fixture(scope='session')
async def db_connection():
    """Фикстура устанавливает соединение с базой данных на все время активности сессии."""
    pg_conn = await asyncpg.connect(**DSL)
    yield pg_conn
    await pg_conn.close()


@backoff.on_exception(
    backoff.expo,
    (
        ConnectionRefusedError,
        aiohttp.client.ClientConnectorError,
        aiohttp.client.ClientError,
    ),
)
@pytest_asyncio.fixture(scope='session')
async def api_session():
    """Фикстура инициализирует клиентскую сессию."""
    session = aiohttp.ClientSession(f'http://{APP_SETTINGS.host}:{APP_SETTINGS.port}', trust_env=True)
    yield session
    await session.close()
