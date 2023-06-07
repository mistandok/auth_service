"""Модуль проверяет состояине Elasticsearch."""

import sys

import backoff
import psycopg2
from psycopg2 import OperationalError

from settings import DSL


@backoff.on_exception(backoff.expo, OperationalError)
def wait_psql():
    conn = psycopg2.connect(**DSL)
    conn.close()


if __name__ == '__main__':
    print('waiting for PostgreSQL...', file=sys.stdout)
    wait_psql()
    print('PostgreSQL was started', file=sys.stdout)
