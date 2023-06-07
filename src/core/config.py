"""Модуль содержит основные настройки для сервиса аутентификации."""

import os
from datetime import timedelta
from functools import cached_property
from pathlib import Path

from pydantic import BaseSettings, Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DEBUG_ENV = os.path.join(BASE_DIR, 'src', 'core', '.env.dev')
PROD_ENV = os.path.join(BASE_DIR, 'docker_app', 'config', 'auth', '.env.prod.dev')

project_env = DEBUG_ENV


class DataBaseSettings(BaseSettings):
    """Класс настроек для подключения к БД"""

    redis_host: str = Field(..., env='REDIS_HOST')
    redis_port: int = Field(..., env='REDIS_PORT')

    refresh_redis_host: str = Field(..., env='REFRESH_REDIS_HOST')
    refresh_redis_port: int = Field(..., env='REFRESH_REDIS_PORT')

    rate_limit_redis_host: str = Field(..., env='RATE_LIMIT_REDIS_HOST')
    rate_limit_redis_port: int = Field(..., env='RATE_LIMIT_REDIS_PORT')

    oauth_redis_host: str = Field(..., env='OAUTH_REDIS_HOST')
    oauth_redis_port: int = Field(..., env='OAUTH_REDIS_PORT')

    jaeger_host: str = Field(..., env='JAEGER_HOST')
    jaeger_port: int = Field(..., env='JAEGER_PORT')
    jaeger_telemetry_sdk_language: str = Field(..., env='JAEGER_TELEMETRY_SDK_LANGUAGE')
    jaeger_telemetry_sdk_name: str = Field(..., env='JAEGER_TELEMETRY_SDK_NAME')
    jaeger_telemetry_sdk_version: str = Field(..., env='JAEGER_TELEMETRY_SDK_VERSION')
    jaeger_service_name: str = Field(..., env='JAEGER_SERVICE_NAME')

    pg_dsn: str = Field(..., env='PG_DSN')
    pg_username: str = Field(..., env='PG_DB_USERNAME')
    pg_password: str = Field(..., env='PG_DB_PASSWORD')
    pg_host: str = Field(..., env='PG_DB_HOST')
    pg_port: str = Field(..., env='PG_DB_PORT')
    pg_name: str = Field(..., env='PG_DB_NAME')
    pg_schema: str = Field(..., env='PG_SCHEMA')

    admin: str = Field(..., env='ADMIN_CONFIG')

    class Config:
        env_file = project_env


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
        env_file = project_env


class AppSettings(BaseSettings):
    """Класс настроек для приложения"""

    host: str = Field(..., env='APP_HOST')
    port: int = Field(..., env='APP_PORT')
    debug: str = Field(..., env='APP_DEBUG')
    test: str = Field(..., env='APP_TEST')

    api_prefix_v1: str = Field(..., env='API_PREFIX_V1')

    class Config:
        env_file = project_env


class VKParams(BaseSettings):
    """Класс настроек для `VK`-клиента."""

    client_id: str = Field(..., env='VK_ID_APP')
    client_secret: str = Field(..., env='VK_SECRET_KEY')
    authorize_url: str = Field(..., env='VK_AUTHORIZE_URL')
    access_token_url: str = Field(..., env='VK_ACCESS_TOKEN_URL')
    base_url: str = Field(..., env='VK_BASE_URL')

    class Config:
        env_file = project_env


class YandexParams(BaseSettings):
    """Класс настроек для `Yandex`-клиента."""

    client_id: str = Field(..., env='Y_ID_APP')
    client_secret: str = Field(..., env='Y_SECRET_KEY')
    authorize_url: str = Field(..., env='Y_AUTHORIZE_URL')
    access_token_url: str = Field(..., env='Y_ACCESS_TOKEN_URL')
    base_url: str = Field(..., env='Y_BASE_URL')

    class Config:
        env_file = project_env


class BaseParamsCode(BaseSettings):
    """Базовый класс для дочерних классов с обязательными атрибутами для генерации уникального `CODE`."""

    response_type: str = Field(..., env='RESPONSE_TYPE')
    redirect_uri: str = Field(..., env='REDIRECT_URI')

    class Config:
        env_file = project_env


class VKParamsCode(BaseParamsCode):
    """`VK`-класс для получения уникального `CODE`."""

    scope: str = Field(..., env='VK_SCOPE')
    v: str = Field(..., env='VK_VERSION')

    class Config:
        env_file = project_env


class YandexParamsCode(BaseParamsCode):
    """`YANDEX`-класс для получения уникального `CODE`."""

    client_id: str = Field(..., env='Y_ID_APP')

    class Config:
        env_file = project_env


class BaseParamsToken(BaseSettings):
    """Базовый класс с обязательными атрибутами для получения токена."""

    grant_type: str = Field(..., env='TOKEN_BODY_GRANT_TYPE')
    redirect_uri: str = Field(..., env='REDIRECT_URI')

    class Config:
        env_file = project_env


DB_SETTINGS = DataBaseSettings()
JWT_SETTINGS = JWTSettings()
APP_SETTINGS = AppSettings()

VK_CONFIG = dict(VKParams())
Y_CONFIG = dict(YandexParams())
