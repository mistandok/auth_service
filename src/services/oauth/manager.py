"""Модуль обработки данных пользователей, залогиневшихся через соц. сеть по OAuth2.0"""

from db import oauth_tokens_storage, transaction
from schemes import oauth_tokens_schema, OAuthTokensSchema
from services.auth.auth import create_tokens
from services.logs import logs
from services.permissions.config import RoleName
from services.role.utils import get_user_roles
from services.user.utils import (
    get_user_by_email, add_roles_to_user, create_user_by_oauth_user_info,
    create_oauth_user, generate_email
)
from .constants import CompleteAnswer
from .interfaces import AuthenticatedUserInfo
from .parsers import OAuthUserParserFactory
from .utils import (generate_access_token_key_to_oauth_user,
                    generate_refresh_token_key_to_oauth_user, get_user_by_oauth_user)
from ..jaeger.tracer import set_trace_by_span_name
from ..user_history.utils import create_user_history
from ..utils import exclude_for_test

logger = logs.get_logger()


class OAuthUserManager:
    """Класс авторизации пользователя в сервисе, прошедшего аутентификация через OAuth."""

    def __init__(self, provider: str, oauth_user_info: dict) -> None:
        self._provider = provider
        self._parser = OAuthUserParserFactory.get_parser_by_provider(self._provider, oauth_user_info)
        self._oauth_user_info = self._parser.parse()
        self._user = None
        self._tokens_response = None

    def auth_user_from_oauth(self) -> OAuthTokensSchema:
        """
        Метод запускает OAuth-обработчиков по данным, полученных от аутентифицированного через OAuth пользователя:
            1) сгенерированные токены + сообщение
            2) сохраняет токены от OAuth-клиента
        Происходит авторизация пользователя в нашем сервисе

        Returns:
            OAuthTokensSchema: access_token, refresh_token и сообщение для пользователя
        """
        transaction(self._auth_user)
        self._save_provider_tokens_in_storage()

        return self._tokens_response

    def _auth_user(self) -> None:
        """Метод авторизовывает пользователя"""
        self._user = get_user_by_oauth_user(self._oauth_user_info.client_id)

        if self._user:
            self._auth_existing_oauth_user()
        else:
            self._auth_new_oauth_user()

        create_user_history(self._user, self._oauth_user_info.user_agent)

    def _auth_existing_oauth_user(self):
        """Метод аутентифицирует и авторизовывает oauth-пользователя, привязанного к пользователю в нашей базе."""
        at, rt = self._create_tokens()
        self._generate_response(at, rt, CompleteAnswer.EXIST_USER.value.format(login=self._user.login))

    def _auth_new_oauth_user(self):
        """Метод аутентифицирует и авторизовывает oauth-пользователя, не привязанного к пользователю в нашей базе."""
        self._user = get_user_by_email(self._oauth_user_info.email)

        if not self._user:
            self._user = create_user_by_oauth_user_info(self._oauth_user_info)
            add_roles_to_user(user_id=self._user.id, role_names=[RoleName.USER.value])

        oauth_user_params = self._prepare_data_for_create_oauth_user()
        create_oauth_user(oauth_user_params)

        at, rt = self._create_tokens()
        self._generate_response(at, rt, message=CompleteAnswer.NEW_USER.value)

    def _prepare_data_for_create_oauth_user(self) -> dict:
        """Метод подготавливает данные для создания oauth_user."""
        return dict(
            email=self._oauth_user_info.email or generate_email(8),
            client_id=self._oauth_user_info.client_id,
            tag=self._provider,
            user_id=self._user.id
        )

    def _create_tokens(self) -> tuple[str, str]:
        """Метод создаёт `access` и `refresh` токены сервиса аутентифицированному через OAuth пользователю"""

        user_roles = get_user_roles(self._user.id)
        roles_name = [role.get('name') for role in user_roles]

        at, rt = create_tokens(
            user_id=self._user.id,
            user_agent=self._oauth_user_info.user_agent,
            user_roles=roles_name or [RoleName.USER.value],
            user_email=self._user.email,
        )
        return at, rt

    def _generate_response(self, at: str, rt: str, message: str) -> None:
        """Метод генерирует `response`-ответ пользователю"""
        self._tokens_response = oauth_tokens_schema.dump(
            dict(
                access_token=at,
                refresh_token=rt,
                message=message,
            )
        )

    def _save_provider_tokens_in_storage(self) -> None:
        """Метод сохраняет `access_token` и `refresh_token` аутентифицированного через OAuth пользователя в кэш"""

        if self._oauth_user_info.access_token:
            access_token_key = generate_access_token_key_to_oauth_user(self._provider, self._user.id)

            oauth_tokens_storage.put(
                key=access_token_key,
                data=self._oauth_user_info.access_token,
                expire=self._oauth_user_info.access_token_expire,
            )

        if self._oauth_user_info.refresh_token:
            refresh_token_key = generate_refresh_token_key_to_oauth_user(self._provider, self._user.id)

            oauth_tokens_storage.put(
                key=refresh_token_key,
                data=self._oauth_user_info.refresh_token,
                expire=self._oauth_user_info.refresh_token_expire,
            )


def proxy_auth_oauth_client(user_info: AuthenticatedUserInfo) -> OAuthTokensSchema:
    """Метод возвращает подтверждение об успешной авторизации на сервисе."""
    exclude_for_test(set_trace_by_span_name)('access_token_url')
    oauth_user_info = user_info.auth_client.get_oauth_user_info(user_info.code)
    oauth_user_info['user_agent'] = user_info.user_agent
    response = OAuthUserManager(user_info.provider, oauth_user_info).auth_user_from_oauth()

    return response
