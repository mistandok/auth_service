"""Модуль содержит в себе API для работы с ролями."""

from http import HTTPStatus

from flask import Blueprint, Flask
from flask_restful import Resource, Api
from flask_jwt_extended import jwt_required, get_jwt
from jwt.exceptions import PyJWTError

from schemes import permission_response_schema, PermissionsResponseSchema
from services.circuit_breaker.circuit import circuit_breaker
from services.http_exceptions.decorators import http_exceptions_handler
from services.http_exceptions.common_exceptions import MissingEntity
from services.request_parser import get_request_params, ParserParam
from services.permissions.utils import get_user_permissions_by_scope
from services.utils import fallback_exception_response

user_permissions_blueprint = Blueprint('permissions', __name__)
api = Api(user_permissions_blueprint, errors=Flask.errorhandler)


class UserPermissionsAPI(Resource):
    """Класс для запросов связанных с разрешениями."""

    @circuit_breaker(fallback_function=fallback_exception_response, excluded_exceptions=(PyJWTError,))
    @jwt_required(optional=True, fresh=True)
    @http_exceptions_handler()
    def get(self) -> tuple[PermissionsResponseSchema, HTTPStatus]:
        """
        Метод, который получает разрешения пользователя
        на определённую область (scope).
        Ручка может работать как с переданным токеном, так и без.
        Если токен передали - то выдаем разрешения для пользователя по `id` из токена,
        если нет - то мы считаем таких пользователей с ролью `incognito` и выдаем соответствующие разрешения.

        Args:
            access_token [optional]: токен доступа пользователя
            scope: область разрешения

        Returns:
            словарь с разрешениями пользователя на данную область (scope)"""

        request_body = get_request_params(
            ParserParam('scope', dict(type=str, location='args'))
        )

        scope = request_body.get('scope')
        if not scope:
            raise MissingEntity('Не передано имя области разрешения.', HTTPStatus.BAD_REQUEST)

        token_data = get_jwt()
        user_id = token_data.get('sub').get('user_id') if token_data else None

        permissions = get_user_permissions_by_scope(scope, user_id)

        return permission_response_schema.dump(dict(**permissions)), HTTPStatus.OK


api.add_resource(UserPermissionsAPI, '/')
