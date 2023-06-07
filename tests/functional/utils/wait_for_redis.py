"""Модуль проверяет состояние Redis."""

import sys

import backoff
from redis import Redis
from redis.exceptions import ConnectionError

from settings import DB_SETTINGS


@backoff.on_exception(backoff.expo, ConnectionError)
def wait_redis_blocklist():
    redis_client = Redis(host=DB_SETTINGS.redis_host, port=DB_SETTINGS.redis_port)
    if not redis_client.ping():
        raise ConnectionError
    redis_client.close()


@backoff.on_exception(backoff.expo, ConnectionError)
def wait_redis_refresh_list():
    redis_client = Redis(host=DB_SETTINGS.refresh_redis_host, port=DB_SETTINGS.refresh_redis_port)
    if not redis_client.ping():
        raise ConnectionError
    redis_client.close()


if __name__ == '__main__':
    print('waiting for Redis...', file=sys.stdout)
    wait_redis_blocklist()
    wait_redis_refresh_list()
    print('Redis was started', file=sys.stdout)
