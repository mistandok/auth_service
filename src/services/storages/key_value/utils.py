"""Модуль содержит различные утилиты, которые помогают в работе с ke/value хранилищами"""
from redis import Redis

from .exceptions import MissKeyValueInterfaceRealisation
from .redis_storage import RedisStorage


def get_key_value_storage_by_client(client):
    """
    Фабрика хранилищ.

    Args:
        client: клиент хранилища.
    """

    if isinstance(client, Redis):
        return RedisStorage(client)

    raise MissKeyValueInterfaceRealisation(client)


def generate_key(*args, **kwargs):
    """
    Метод генерирует ключ для хранилища на основе параметров.

    Args:
          args: позиционные аргументы.
          kwargs: именованные аргументы.
    """
    return f'{args}_{kwargs}'
