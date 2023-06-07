"""Модуль содержит основные настройки для сервиса аутентификации."""

import os
from datetime import timedelta
from functools import cached_property
from pathlib import Path

from pydantic import BaseSettings, Field

BASE_DIR = Path(__file__).resolve().parent.parent


class DataBaseSettings(BaseSettings):
    """Класс настроек для подключения к БД"""

    redis_host: str = Field(..., env='REDIS_HOST')
    redis_port: int = Field(..., env='REDIS_PORT')

    refresh_redis_host: str = Field(..., env='REFRESH_REDIS_HOST')
    refresh_redis_port: int = Field(..., env='REFRESH_REDIS_PORT')

    pg_dsn: str = Field(..., env='PG_DSN')
    pg_username: str = Field(..., env='PG_DB_USERNAME')
    pg_password: str = Field(..., env='PG_DB_PASSWORD')
    pg_host: str = Field(..., env='PG_DB_HOST')
    pg_port: str = Field(..., env='PG_DB_PORT')
    pg_name: str = Field(..., env='PG_DB_NAME')
    pg_schema: str = Field(..., env='PG_SCHEMA')

    admin: str = Field(..., env='ADMIN_CONFIG')

    class Config:
        env_file = os.path.join(BASE_DIR, 'functional', '.env.dev')


class JWTSettings(BaseSettings):
    """Класс настроек для JWT-токенов"""

    secret_key: str = Field(..., env='JWT_SECRET_KEY')
    hidden_access_token_expires: int = Field(..., env='JWT_ACCESS_TOKEN_EXPIRES')
    hidden_refresh_token_expires: int = Field(..., env='JWT_REFRESH_TOKEN_EXPIRES')

    @cached_property
    def access_token_expires(self) -> timedelta:
        """Метод определяет время жизни access-токена"""
        return timedelta(minutes=self.hidden_access_token_expires)

    @cached_property
    def refresh_token_expires(self) -> timedelta:
        """Метод определяет время жизни refresh-токена"""
        return timedelta(days=self.hidden_refresh_token_expires)

    class Config:
        keep_untouched = (cached_property,)
        env_file = os.path.join(BASE_DIR, 'functional', '.env.dev')


class AppSettings(BaseSettings):
    """Класс настроек для приложения"""

    host: str = Field(..., env='APP_HOST')
    port: int = Field(..., env='APP_PORT')

    class Config:
        env_file = os.path.join(BASE_DIR, 'functional', '.env.dev')


DB_SETTINGS = DataBaseSettings()
JWT_SETTINGS = JWTSettings()
APP_SETTINGS = AppSettings()

DSL = {
    'database': DB_SETTINGS.pg_name,
    'user': DB_SETTINGS.pg_username,
    'password': DB_SETTINGS.pg_password,
    'host': DB_SETTINGS.pg_host,
    'port': DB_SETTINGS.pg_port
}
