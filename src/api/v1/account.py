"""Модуль содержит в себе api для работы с auth пользователей."""
from datetime import timedelta
from http import HTTPStatus

from flask import Blueprint, Flask
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required, get_jwt
)
from flask_restful import Resource, Api
from jwt import PyJWTError

from db import transaction, tat_storage
from db_models import User
from schemes import (
    TokensSchema, BaseResponseSchema, AccessTokenSchema, ListResponseSchema,
    base_schema, tokens_schema, access_token_schema
)
from services.auth import auth
from services.circuit_breaker.circuit import circuit_breaker
from services.http_exceptions.decorators import http_exceptions_handler
from services.logs import logs
from services.rate_limit.gcra import rate_limit_requests
from services.request_parser import limit_type, ParserParam, get_request_params
from services.user_history.utils import get_user_history_list
from services.utils import fallback_exception_response

logger = logs.get_logger()

account_blueprint = Blueprint('account', __name__)
api = Api(account_blueprint, errors=Flask.errorhandler)


class SignUpAPI(Resource):
    """Класс-API для регистрации нового пользователя."""

    @circuit_breaker(fallback_function=fallback_exception_response)
    @http_exceptions_handler()
    @rate_limit_requests(tat_storage=tat_storage, limit_requests=100, period=timedelta(seconds=60))
    def post(self) -> tuple[BaseResponseSchema, HTTPStatus]:
        """
            Метод осуществляет регистрацию пользователя
            и добавляет ему роль `user`.
            """
        request_body = get_request_params(
            ParserParam('login', dict(type=str, location='json', required=True)),
            ParserParam('email', dict(type=str, location='json', required=True)),
            ParserParam('password', dict(type=str, location='json', required=True)),
            ParserParam('first_name', dict(type=str, location='json')),
            ParserParam('surname', dict(type=str, location='json')),
            ParserParam('patronymic', dict(type=str, location='json')),
        )

        user = User(**request_body)

        transaction(auth.sign_up, user)

        return base_schema.dump(dict(
            msg='Пользователь был зарегестрирован!',
        )), HTTPStatus.OK


class LoginAPI(Resource):
    """Класс отвечает за реализацию ручки по идентификации и аутентификации пользователя"""

    @circuit_breaker(fallback_function=fallback_exception_response)
    @http_exceptions_handler()
    @rate_limit_requests(tat_storage=tat_storage, limit_requests=100, period=timedelta(seconds=60))
    def post(self) -> tuple[TokensSchema | BaseResponseSchema, HTTPStatus]:
        """
        Идентификация и аутентификация пользователя.

        В случае успешного прохождения возвращается пара access_token, refresh_token.
        """
        request_body = get_request_params(
            ParserParam('login', dict(type=str, location='json', required=True)),
            ParserParam('password', dict(type=str, location='json', required=True)),
            ParserParam('User-Agent', dict(location='headers')),
        )

        login = request_body.get('login')
        password = request_body.get('password')
        user_agent = request_body.get('User-Agent')

        access_token, refresh_token = transaction(auth.login, login, password, user_agent)

        return tokens_schema.dump(dict(
            access_token=access_token,
            refresh_token=refresh_token,
        )), HTTPStatus.OK


class LogoutAPI(Resource):
    """Класс позволяет осуществить logout пользователя."""

    @circuit_breaker(fallback_function=fallback_exception_response, excluded_exceptions=(PyJWTError,))
    @jwt_required(fresh=True)
    @http_exceptions_handler()
    @rate_limit_requests(tat_storage=tat_storage, limit_requests=100, period=timedelta(seconds=60))
    def delete(self) -> tuple[BaseResponseSchema, HTTPStatus]:
        """Метод осуществялет logout пользователя."""
        jwt_payload = get_jwt()

        auth.logout(jwt_payload)

        return base_schema.dump(dict(
            msg='Access-token и Refresh-token теперь в блоклисте и более недоступны.',
        )), HTTPStatus.OK


class RefreshAPI(Resource):
    """Класс позволяет осуществить рефреш токенов"""

    @circuit_breaker(fallback_function=fallback_exception_response, excluded_exceptions=(PyJWTError,))
    @jwt_required(refresh=True)
    @http_exceptions_handler()
    @rate_limit_requests(tat_storage=tat_storage, limit_requests=100, period=timedelta(seconds=60))
    def get(self) -> tuple[AccessTokenSchema, HTTPStatus]:
        """Метод предоставляет новый аксесс токен, если приходит валидный рефреш токен."""
        refresh_token = get_jwt()
        identity = get_jwt_identity()

        access_token = auth.refresh(refresh_token, identity)

        return access_token_schema.dump(dict(
            access_token=access_token
        )), HTTPStatus.OK


class UserHistoryAPI(Resource):
    """Класс позволяет осуществить поиск информации о входах пользователя."""

    @circuit_breaker(fallback_function=fallback_exception_response, excluded_exceptions=(PyJWTError,))
    @jwt_required(fresh=True)
    @http_exceptions_handler()
    @rate_limit_requests(tat_storage=tat_storage, limit_requests=100, period=timedelta(seconds=60))
    def get(self) -> tuple[ListResponseSchema | BaseResponseSchema, HTTPStatus]:
        """Метод предоставляет информацию о истории входов пользователя."""
        request_body = get_request_params(
            ParserParam('limit', dict(type=limit_type, location='args')),
            ParserParam('search_after', dict(type=str, location='args', action='append')),
        )

        jwt_payload = get_jwt()

        user_id = jwt_payload.get('sub').get('user_id')
        limit = request_body.get('limit')
        search_after = request_body.get('search_after')

        history = get_user_history_list(user_id, limit, search_after)

        return history, HTTPStatus.OK


class UpdateUserAuthDataAPI(Resource):
    """Класс позволяет осуществить обновления аутентификационных данных для пользователя."""

    @circuit_breaker(fallback_function=fallback_exception_response, excluded_exceptions=(PyJWTError,))
    @jwt_required(fresh=True)
    @http_exceptions_handler()
    @rate_limit_requests(tat_storage=tat_storage, limit_requests=100, period=timedelta(seconds=60))
    def patch(self) -> tuple[BaseResponseSchema, HTTPStatus]:
        """Метод осуществляет обновление аутентификационных данных для пользователя"""
        request_body = get_request_params(
            ParserParam('login', dict(type=str, location='json')),
            ParserParam('password', dict(type=str, location='json')),
        )

        jwt_payload = get_jwt()

        user_id = jwt_payload.get('sub').get('user_id')
        new_login = request_body.get('login')
        new_password = request_body.get('password')

        transaction(auth.update_auth_data, user_id, new_login, new_password)

        return base_schema.dump(dict(
            msg='Аутентификационные данные успешно обновлены!',
        )), HTTPStatus.OK


class UserAgentLogoutAPI(Resource):
    """Класс позволяет осуществить логаут с выбранных устройств."""

    @circuit_breaker(fallback_function=fallback_exception_response, excluded_exceptions=(PyJWTError,))
    @jwt_required(fresh=True)
    @http_exceptions_handler()
    @rate_limit_requests(tat_storage=tat_storage, limit_requests=100, period=timedelta(seconds=60))
    def post(self):
        """
        Метод осуществляет логаут для указанных устройств.

        Если в параметре 'user_agents_for_logout' будет передано значение ['all'],
        то произойдет логаут всех активных сессий. Иначе пройдем по списку сессий и выйдем только из тех, которые
        в нем указаны.
        """
        request_body = get_request_params(
            ParserParam('user_agents_for_logout', dict(type=list, location='json', required=True)),
        )

        jwt_payload = get_jwt()

        user_id = jwt_payload.get('sub', {}).get('user_id')
        user_agents_for_logout = request_body.get('user_agents_for_logout', [])

        auth.logout_user_for_user_agents(user_id, user_agents_for_logout)

        return base_schema.dump(dict(
            msg='Выбранные сессии были завершены',
        )), HTTPStatus.OK


api.add_resource(SignUpAPI, '/signup')
api.add_resource(LoginAPI, '/login')
api.add_resource(RefreshAPI, '/refresh')
api.add_resource(LogoutAPI, '/logout')
api.add_resource(UserHistoryAPI, '/history-auth/')
api.add_resource(UpdateUserAuthDataAPI, '/update-auth-data/')
api.add_resource(UserAgentLogoutAPI, '/logout-from-devices/')
