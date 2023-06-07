"""Модуль инициализирует подключение к БД."""

from redis import Redis
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.schema import CreateSchema

from core.config import DB_SETTINGS
from services.storages.key_value.redis_storage import RedisStorage
from services.storages.key_value.utils import get_key_value_storage_by_client

Base = declarative_base()

engine = create_engine(DB_SETTINGS.pg_dsn)
schema = DB_SETTINGS.pg_schema

if not engine.dialect.has_schema(connect := engine.connect(), schema):
    with connect as connection:
        connection.execute(CreateSchema(schema))
        connection.commit()

Base.metadata.create_all(engine)


blocklist_client = Redis(host=DB_SETTINGS.redis_host, port=DB_SETTINGS.redis_port, decode_responses=True)
refresh_list_client = Redis(
    host=DB_SETTINGS.refresh_redis_host, port=DB_SETTINGS.refresh_redis_port, decode_responses=True
)
oauth_client = Redis(
    host=DB_SETTINGS.oauth_redis_host, port=DB_SETTINGS.oauth_redis_port, decode_responses=True
)

blocklist: RedisStorage = get_key_value_storage_by_client(blocklist_client)
refresh_list: RedisStorage = get_key_value_storage_by_client(refresh_list_client)
oauth_tokens_storage: RedisStorage = get_key_value_storage_by_client(oauth_client)

tat_storage: Redis = Redis(
    host=DB_SETTINGS.rate_limit_redis_host, port=DB_SETTINGS.rate_limit_redis_port, decode_responses=True
)

db_session = scoped_session(sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
))

Base.query = db_session.query_property()


def transaction(func: callable, *args, **kwargs):
    """
    Функция запускает другую функцию в транзакции.

    Args:
        func: callable объект, который нужно запустить в транзакции.
    """
    try:
        result = func(*args, **kwargs)
        db_session.commit()
        return result
    except Exception as error:
        db_session.rollback()
        raise error
