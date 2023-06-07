"""Модуль содержит различные тестовые данные для ролей."""

from collections import namedtuple
from http import HTTPStatus

from tests.functional.settings import DB_SETTINGS


def get_test_user_data_denied() -> list:
    """Функция генерирует тестовые данные для тестирования ручек ролей."""
    TestData = namedtuple('TestData', ['user', 'expected_status'])
    return [
        TestData(
            user=DB_SETTINGS.admin,
            expected_status=HTTPStatus.OK
        ),
        TestData(
            user='test_user',
            expected_status=HTTPStatus.FORBIDDEN
        )
    ]


def get_test_user_data_allowed() -> list:
    """Функция генерирует тестовые данные для тестирования ручек ролей."""
    TestData = namedtuple('TestData', ['user', 'expected_status'])
    return [
        TestData(
            user=DB_SETTINGS.admin,
            expected_status=HTTPStatus.OK
        ),
        TestData(
            user='test_user',
            expected_status=HTTPStatus.OK
        )
    ]


def get_test_user_data_denied_incorrect() -> list:
    """Функция генерирует тестовые данные для тестирования ручек ролей."""
    TestData = namedtuple('TestData', ['user', 'expected_status'])
    return [
        TestData(
            user=DB_SETTINGS.admin,
            expected_status=HTTPStatus.NOT_FOUND
        ),
        TestData(
            user='test_user',
            expected_status=HTTPStatus.FORBIDDEN
        )
    ]


def get_test_user_data_allowed_incorrect() -> list:
    """Функция генерирует тестовые данные для тестирования ручек ролей."""
    TestData = namedtuple('TestData', ['user', 'expected_status'])
    return [
        TestData(
            user=DB_SETTINGS.admin,
            expected_status=HTTPStatus.NOT_FOUND
        ),
        TestData(
            user='test_user',
            expected_status=HTTPStatus.NOT_FOUND
        )
    ]


def get_test_user_data_denied_incorrect_add_role() -> list:
    """Функция генерирует тестовые данные для тестирования ручек ролей."""
    TestData = namedtuple('TestData', ['user', 'expected_status'])
    return [
        TestData(
            user=DB_SETTINGS.admin,
            expected_status=HTTPStatus.CONFLICT
        ),
        TestData(
            user='test_user',
            expected_status=HTTPStatus.FORBIDDEN
        )
    ]


def get_test_user_data_denied_incorrect_del_role() -> list:
    """Функция генерирует тестовые данные для тестирования ручек ролей."""
    TestData = namedtuple('TestData', ['user', 'expected_status'])
    return [
        TestData(
            user=DB_SETTINGS.admin,
            expected_status=HTTPStatus.BAD_REQUEST
        ),
        TestData(
            user='test_user',
            expected_status=HTTPStatus.FORBIDDEN
        )
    ]
