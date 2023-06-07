"""Модуль содержит реализацию хранилища на основе Редис клиента"""
from datetime import timedelta

from .interfaces import BaseKeyValueStorage


class RedisStorage(BaseKeyValueStorage):
    """Класс для работы с хранилищем редис"""

    def get(self, key):
        return self._client.get(key)

    def get_by_template(self, template: str):
        for key in self._client.scan_iter(template):
            yield key, self._client.get(key)

    def delete(self, key):
        self._client.delete(key)

    def put(self, key, data, expire: int | timedelta | None = None):
        self._client.set(key, data, expire)
