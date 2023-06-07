"""Модуль парсеров информации аутентифицированных пользователей"""

from datetime import timedelta

from services.http_exceptions.common_exceptions import MissingRealization
from services.oauth.client import oauth_clients
from services.oauth.constants import ProviderName
from services.oauth.interfaces import BaseParserUser, OAuthUserInfo


class VKParserUser(BaseParserUser):
    """Класс-парсер для аутентифицированного через VK OAuth пользователя."""

    def parse(self) -> OAuthUserInfo:
        """Метод собирает информацию о пользователе."""
        return OAuthUserInfo(
            email=self._oauth_user_info.get('email'),
            client_id=self._oauth_user_info.get('user_id'),
            access_token=self._oauth_user_info.get('access_token'),
            refresh_token=self._oauth_user_info.get('refresh_token'),
            user_agent=self._oauth_user_info.get('user_agent'),
            access_token_expire=timedelta(seconds=self._oauth_user_info.get('expires_in')),
            refresh_token_expire=timedelta(seconds=self._oauth_user_info.get('expires_in')),
        )


class YandexParserUser(BaseParserUser):
    """Класс-парсер для аутентифицированного через Yandex OAuth пользователя."""

    def __init__(self, oauth_user_info: dict) -> None:
        super().__init__(oauth_user_info)
        self._actual_user_info = self._get_info_from_yandex()

    def parse(self) -> OAuthUserInfo:
        """Метод собирает информацию о пользователе."""
        return OAuthUserInfo(
            email=self._actual_user_info.get('default_email'),
            client_id=self._actual_user_info.get('id'),
            access_token=self._oauth_user_info.get('access_token'),
            refresh_token=self._oauth_user_info.get('refresh_token'),
            user_agent=self._oauth_user_info.get('user_agent'),
            access_token_expire=timedelta(seconds=self._oauth_user_info.get('expires_in')),
            refresh_token_expire=timedelta(seconds=self._oauth_user_info.get('expires_in')),
        )

    def _get_info_from_yandex(self) -> dict:
        """Метод получает доступ к персональной информации пользователя."""

        access_token = self._oauth_user_info.get('access_token')

        session = oauth_clients()[ProviderName.YANDEX.value].get_session(access_token)
        info = session.get('https://login.yandex.ru/info').json()
        return info


class OAuthUserParserFactory:
    providers = {
        ProviderName.VK.value: VKParserUser,
        ProviderName.YANDEX.value: YandexParserUser
    }

    @staticmethod
    def get_parser_by_provider(provider, *args, **kwargs) -> BaseParserUser:
        """Метод возвращает парсер-класс в зависимости от задаваемого провайдера"""
        try:
            return OAuthUserParserFactory.providers[provider](*args, **kwargs)
        except KeyError:
            raise MissingRealization(f'OAuth {provider=} на сервисе не поддерживает!')
