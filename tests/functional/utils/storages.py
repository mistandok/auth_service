"""Объекты для работы с хранилищами."""

from typing import Iterable

import aioredis
import backoff
import orjson
from aioredis import Redis


@backoff.on_exception(backoff.expo, aioredis.RedisError)
async def get_item_from_cache(redis_client: Redis, cached_id: str):
    """Функция отвечает за получение объекта из кэша по `cache_id`."""

    result: bytes = await redis_client.get(cached_id)
    if result:
        return orjson.loads(result)
    return {}
