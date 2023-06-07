"""Модуль для инициализаии парсера запросов."""
from dataclasses import dataclass
from types import NoneType

from flask_restful import reqparse

parser = reqparse.RequestParser()


@dataclass
class ParserParam:
    name: str
    params: dict


def get_request_params(*params: ParserParam) -> dict:
    """
    Функция позволяет получить заданные параметры из запроса.

    Args:
        params: параметры, которые могут быть в запросе.

    Returns:
        dict - параметры.
    """
    parser_copy = parser.copy()

    for param in params:
        parser_copy.add_argument(param.name, **param.params)

    return parser_copy.parse_args()


def limit_type(value):
    try:
        value = int(value)
    except ValueError:
        raise ValueError('Лимит должен быть целым числом.')
    if value <= 0 or value > 50:
        raise ValueError('Лимит должен быть в допустимом диапазоне [1:50].')
    return value


def page_type(value):
    try:
        value = int(value)
    except ValueError as err:
        raise TypeError('Тип номера страницы задан неверно.') from err
    if value < 1:
        raise ValueError('Номер страницы задан неверно. Допустимые значения от 1')
    return value
