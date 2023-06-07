"""
Модуль реализует ratelimit c помощью алгоритма GCRA (https://en.wikipedia.org/wiki/Generic_cell_rate_algorithm).

GCRA отслеживает оставшийся лимит с помощью так называемого теоретического времени прибытия
(Theoretical Arrival Time, TAT) каждого запроса:

tat = current_time + period

Алгоритм ограничивает следующий запрос, если время прибытия меньше текущего ТАТ. Это хорошо работает,
если частота равна 1 запрос/период, когда запросы разделены по периодам.
Но в реальности частоты обычно вычисляется как лимит/период. Например, если частота равна 10 запросов/60 сек,
то пользователю можно будет делать 10 запросов в первые 6 секунд.
А с частотой 1 запрос/6 сек ему придётся ждать по 6 секунд между запросами.

Чтобы иметь возможность отправлять в течение короткого периода группу запросов и
поддерживать ограничение их количества за период с лимитом > 1
каждый запрос нужно разделить отношением период/лимит, и тогда следующее теоретическое время прибытия
(new_tat) будет вычисляться иначе.

Обозначим время прибытия запроса как t:

new_tat = tat + period / limit, если запросы объединяются в группу (t <= tat)
new_tat = t + period / limit, если запросы не объединяются в группу (t > tat)

Следовательно:

new_tat = max(tat, t) + period / limit

Запрос будет ограничен, если new_tat превышает сумму текущего времени и периода:

new_tat > t + period. При new_tat = tat + period / limit мы получаем tat + period / limit > t + period.

Следовательно, нужно ограничивать запросы только при tat - t > period - period / limit.
"""
from datetime import timedelta
from functools import wraps
from http import HTTPStatus

from flask_jwt_extended import get_jwt
from redis import Redis
from services.http_exceptions.common_exceptions import TooManyRequests


def rate_limit_requests(tat_storage: Redis, limit_requests: int, period: timedelta):
    """
    Декоратор для методов классов flask_restful, который обеспечивает ограничение запросов к ручке по алгоритму GCRA.

    Если limit_requests = 10, a period = 60 секунд, то можно делать 10 запросов в первые 6 секунд.
    Args:
        tat_storage: хранилище редис, в котором для ключа будет хранится время TAT.
        limit_requests: максимально допустимое количество запросов.
        period: период, за который допустимо это количество запросов.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            class_name = self.__class__.__name__
            func_name = func.__name__
            user_id = _get_user_id()

            tat_key = _get_tat_key(class_name, func_name, user_id)

            period_in_seconds = int(period.total_seconds())
            current_time = tat_storage.time()[0]
            separation = round(period_in_seconds / limit_requests)
            tat_storage.setnx(tat_key, 0)

            try:
                tat = max(int(tat_storage.get(tat_key)), current_time)
                if tat - current_time <= period_in_seconds - separation:
                    new_tat = max(tat, current_time) + separation
                    tat_storage.set(tat_key, new_tat)
                    return func(self, *args, **kwargs)

                raise TooManyRequests('Слишком частые однотипные вызовы метода!', HTTPStatus.TOO_MANY_REQUESTS)
            except LookupError:
                raise TooManyRequests('Слишком частые однотипные вызовы метода!', HTTPStatus.TOO_MANY_REQUESTS)

        return wrapper

    return decorator


def _get_user_id() -> str | None:
    """
    Служебная функция, которая пытается получить ID пользователя, если ручка декорирована jwt.

    Returns:
        user_id: str
    """
    try:
        jwt_payload = get_jwt()
        return str(jwt_payload.get('sub').get('user_id'))
    except RuntimeError:
        return None


def _get_tat_key(class_name: str, method_name: str, user_id: str | None = None) -> str:
    """
    Служебная функция для генерации ключа для времени tat.

    Args:
        class_name: название класса, чей метод декорируем.
        method_name: название метода, который декорируем.
        user_id: ID пользователя, если есть.

    Return:
        tat_ket: str
    """
    return f'{class_name}:{method_name}:{user_id}'
