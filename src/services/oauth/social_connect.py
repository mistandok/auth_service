"""Модуль взаимодействия с OAuth2.0 для разных провайдеров"""
from abc import ABC

import requests

from services.http_exceptions.common_exceptions import MissingRealization
from .client import ClientBuilder
from .constants import ProviderName


class BaseOAuthTemplate(ABC):
    """
    Абстрактный шаблон для реализации OAuth.

    Для работы с классом необходимо задать `builder` в его наследниках.
    """

    builder: ClientBuilder = None

    def __init__(self, model) -> None:
        self.client = model.builder.get_client()

    def get_authorize_url(self) -> str:
        """Метод возвращает ссылку-редирект для получения уникального `CODE`."""

        params = self.builder.get_params_for_code()
        url = self.client.get_authorize_url(**params)
        return url

    def get_oauth_user_info(self, code: int | str) -> dict:
        """Метод возвращает `access_token`."""

        params = self.builder.get_params_for_token(code)
        session = self.client.get_raw_access_token(data=params)
        try:
            return session.json()
        except requests.exceptions.ConnectTimeout:
            raise
        finally:
            session.close()


class VKOauth(BaseOAuthTemplate):
    """Класс для работы с OAuth2.0 от `VK`."""

    builder = ClientBuilder(ProviderName.VK.value)


class YandexOauth(BaseOAuthTemplate):
    """Класс для работы с OAuth2.0 от `YANDEX`."""

    builder = ClientBuilder(ProviderName.YANDEX.value)


class OAuthFactory:
    clients = {
        ProviderName.VK.value: VKOauth,
        ProviderName.YANDEX.value: YandexOauth
    }

    @staticmethod
    def get_client_by_provider(provider: str | None) -> BaseOAuthTemplate:
        """Метод возвращает класс для работы с OAuth2.0 в зависимости от задаваемого провайдера"""
        try:
            return OAuthFactory.clients[provider](OAuthFactory.clients[provider])
        except KeyError:
            raise MissingRealization(f'OAuth {provider=} на сервисе не реализован!')
