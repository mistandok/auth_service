"""Модуль конфигурации для разрешений пользователей."""

from enum import IntEnum, Enum


class AccessLevel(IntEnum):
    """
    Класс описываем маски уровня доступа.

    Эти значения применяются в побитовых операциях для проверки уровня доступа, к примеру:
    Полный доступ: 14('0b1110') (содержит в себе ADMIN (8('0b1000')), WRITE (4('0b100')), READ (2('0b10'))).
    Операция для вычисления уровня доступа:
    is_write_allowed:
    1) 14('0b1110') & 4('0b100') == 4('0b100') (уровень доступа был полным, побитово умножили ег на маску,
    увидели, что она совпадает с маской для записи => да, доступ на запись есть);
    2) 2('0b10') & 4('0b100') != 4('0b100') (уровень доступа был чтение, побитово умножили его на маску,
    увидели, что оне НЕ совпадает с маской для записи => нет, доступа на запись нет)
    """
    ADMIN = 8
    WRITE = 4
    READ = 2


class RoleName(Enum):
    """Класс определяющий имена ролей."""

    ADMIN = 'admin'
    SUBSCRIBER = 'subscriber'
    AMEDIATEKA = 'amediateka'
    USER = 'user'
    INCOGNITO = 'incognito'


class ScopeName(Enum):
    """Класс определяющий имена областей разрешения."""

    FILMS = 'films'
    FILM_DETAIL = 'film_details'
    PERSONS = 'persons'
    PERSON_DETAIL = 'person_details'
    GENRES = 'genres'
    PROTECTED = 'protected'
