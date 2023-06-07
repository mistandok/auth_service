"""Модуль дефолтных значений"""

from enum import Enum


class ProviderName(str, Enum):
    VK = 'vk'
    YANDEX = 'yandex'


class CompleteAnswer(str, Enum):
    """Класс описывает возможные сообщения после логина через соц. сеть."""

    EXIST_USER = 'С возвращением, {login}'
    NEW_USER = 'Вы были успешно зарегистрированы. Для завершения актуализируйте Ваши учётные данные.'
