"""Модуль содержит базовый интерфейс для органихации работы с key/value хранилищами."""
from abc import ABC, abstractmethod
from datetime import timedelta


class BaseKeyValueStorage(ABC):
    """Интерфейс для key-value-хранилищей."""

    def __init__(self, client):
        """
        Инициализирующий метод.
        Args:
            client: клиент хранилища.
        """
        self._client = client

    @abstractmethod
    def get(self, key):
        """
        Абстрактный метод для получения значения по ключу

        Args:
            key (str): ключ
        """
        pass

    @abstractmethod
    def get_by_template(self, template: str):
        """
        Абстрактный метод, для получения значений по шаблону ключа.

        Args:
            template: шаблон ключа.

        Returns:
            метод должен возвращать итерируемый объект, состоящий из пар (ключ, значение)
        """
        pass

    @abstractmethod
    def delete(self, key):
        """
        Абстрактный метод для удаления ключа.

        Args:
            key (str): ключ
        """
        pass

    @abstractmethod
    def put(self, key, data, expire: int | timedelta | None = None):
        """
        Абстрактный метод, для сохранения в хранилище значение по ключу
        Args:
            key (str): ключ
            data (Any): значение
            expire: время жизни записи
        """
        pass
