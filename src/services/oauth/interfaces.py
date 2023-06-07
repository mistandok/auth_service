"""Модуль интерфейсов и датаклассов для работы с OAuth2.0"""

from abc import abstractmethod, ABC
from dataclasses import asdict, dataclass

from pydantic.schema import timedelta

from services.oauth.social_connect import OAuthFactory, BaseOAuthTemplate


@dataclass
class OAuthUserInfo:
    """Класс описывает аутентифицированного пользователя."""
    email: str
    client_id: str
    access_token: str
    refresh_token: str
    user_agent: str
    access_token_expire: timedelta
    refresh_token_expire: timedelta
    tag: str | None = None
    local_user_id: str | None = None

    def as_dict(self) -> dict:
        """Метод возвращает объект словарём."""
        return asdict(self)


@dataclass
class AuthenticatedUserInfo:
    """Класс описывает клиентS-информацию аутентифицированного пользователя."""

    provider: str
    user_agent: str
    code: str
    auth_client: BaseOAuthTemplate = None

    def __post_init__(self):
        self.auth_client = OAuthFactory.get_client_by_provider(self.provider)


class BaseParserUser(ABC):
    """Базовый парсер-класс для наследников по работе с данными аутентифицированного пользователя."""

    def __init__(self, oauth_user_info: dict) -> None:
        self._oauth_user_info = oauth_user_info

    @abstractmethod
    def parse(self) -> OAuthUserInfo:
        pass
