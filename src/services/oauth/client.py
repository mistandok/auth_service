"""Модуль настройки OAuth-клиентов и их параметров для провайдеров"""

from functools import lru_cache

from rauth import OAuth2Service

from core.config import (
    VK_CONFIG, VKParamsCode,
    Y_CONFIG, YandexParamsCode,
    BaseParamsToken, BaseParamsCode
)
from services.oauth.constants import ProviderName


@lru_cache
def oauth_clients() -> dict:
    """Метод возвращает сконфигурированные OAuth-клиентов для провайдеров."""
    vk_client = OAuth2Service(**VK_CONFIG)
    yandex_client = OAuth2Service(**Y_CONFIG)
    return {
        ProviderName.VK.value: vk_client,
        ProviderName.YANDEX.value: yandex_client
    }


@lru_cache
def get_code_config_by_provider(provider: str) -> BaseParamsCode:
    """Метод возвращает параметры OAuth-клиентам для получения уникального `CODE`."""
    routers = {
        ProviderName.VK.value: VKParamsCode,
        ProviderName.YANDEX.value: YandexParamsCode,
    }
    return routers.get(provider)


class ClientBuilder:
    """Класс-сборщик параметров для провайдеров"""

    def __init__(self, provider: str) -> None:
        self._provider = provider

    def get_client(self) -> OAuth2Service:
        """Метод возвращает сконфигурированного OAuth-клиента в зависимости от провайдера"""
        return oauth_clients().get(self._provider)

    def get_params_for_code(self) -> dict:
        """Метод возвращает набор данных в зависимости от провайдера для получения уникального `CODE`"""
        code = dict(get_code_config_by_provider(self._provider)())
        code['redirect_uri'] = code['redirect_uri'].format(provider=self._provider)
        return code

    def get_params_for_token(self, code: int) -> dict:
        """Метод возвращает набор данных в зависимости от провайдера для получения `access-token`"""
        token = dict(BaseParamsToken())

        token.update(
            {
                'code': str(code),
                'redirect_uri': token['redirect_uri'].format(provider=self._provider)
            }
        )
        return token
