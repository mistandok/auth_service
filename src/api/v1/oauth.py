"""Модуль содержит в себе api для работы с auth пользователей."""
from datetime import timedelta

from flask import Response, Blueprint, Flask
from flask import request, redirect
from flask_restful import Resource, Api

from db import tat_storage
from schemes import OAuthTokensSchema

from services.circuit_breaker.circuit import circuit_breaker
from services.jaeger.tracer import set_trace_by_span_name
from services.logs import logs
from services.oauth.constants import ProviderName
from services.oauth.interfaces import AuthenticatedUserInfo
from services.oauth.manager import proxy_auth_oauth_client
from services.oauth.social_connect import OAuthFactory
from services.rate_limit.gcra import rate_limit_requests
from services.utils import fallback_exception_response, exclude_for_test

logger = logs.get_logger()

oauth_blueprint = Blueprint('oauth', __name__)
api = Api(oauth_blueprint, errors=Flask.errorhandler)


class OAuthAPI(Resource):
    """Класс-API для авторизации на сервисе аутентифицированным пользователям через OAuth."""

    @circuit_breaker(fallback_function=fallback_exception_response)
    @rate_limit_requests(tat_storage=tat_storage, limit_requests=100, period=timedelta(seconds=60))
    def get(self, provider: str) -> Response:
        """Метод делает редирект на сторонний сайт для аутентификации."""
        exclude_for_test(set_trace_by_span_name)('oauth')
        auth_client = OAuthFactory.get_client_by_provider(provider)

        exclude_for_test(set_trace_by_span_name)('authorize_url')
        authorize_url = auth_client.get_authorize_url()
        return redirect(authorize_url)


class YandexOAuthAPI(Resource):
    """Класс авторизации аутентифицированных пользователей через Yandex."""

    @circuit_breaker(fallback_function=fallback_exception_response)
    @rate_limit_requests(tat_storage=tat_storage, limit_requests=100, period=timedelta(seconds=60))
    def get(self) -> OAuthTokensSchema:
        """Метод авторизовывает аутентифицированного пользователя."""
        user_info = AuthenticatedUserInfo(
            provider=ProviderName.YANDEX.value,
            code=str(request.args.get('code')),
            user_agent=str(request.user_agent)
        )
        return proxy_auth_oauth_client(user_info)


class VKOAuthAPI(Resource):
    """Класс авторизации аутентифицированных пользователей через VK."""

    @circuit_breaker(fallback_function=fallback_exception_response)
    @rate_limit_requests(tat_storage=tat_storage, limit_requests=100, period=timedelta(seconds=60))
    def get(self) -> OAuthTokensSchema:
        """Метод авторизовывает аутентифицированного пользователя."""
        user_info = AuthenticatedUserInfo(
            provider=ProviderName.VK.value,
            code=str(request.args.get('code')),
            user_agent=str(request.user_agent)
        )
        return proxy_auth_oauth_client(user_info)


api.add_resource(OAuthAPI, '/login/<provider>')
api.add_resource(YandexOAuthAPI, '/yandex/token')
api.add_resource(VKOAuthAPI, '/vk/token')
