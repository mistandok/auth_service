"""Модуль содержит в себе API для работы с ролями."""
from datetime import timedelta
from http import HTTPStatus
from uuid import UUID

from flask import Blueprint, Flask
from flask_restful import Resource, Api
from flask_jwt_extended import jwt_required
from jwt import PyJWTError

from db import transaction, tat_storage
from schemes import base_schema, BaseResponseSchema, RoleSchema
from services.circuit_breaker.circuit import circuit_breaker
from services.http_exceptions.decorators import http_exceptions_handler
from services.rate_limit.gcra import rate_limit_requests
from services.request_parser import get_request_params, ParserParam, limit_type, page_type
from services.role.utils import get_user_roles

from services.user.decorators import admin_required
from services.user.utils import add_roles_to_user, delete_roles_from_user, InfoUsersList
from services.utils import fallback_exception_response, SearchInfoUserParams

users_blueprint = Blueprint('users', __name__)
api = Api(users_blueprint, errors=Flask.errorhandler)


class UserRolesListAPI(Resource):
    """CRUD-класс списочных методов для ролей пользователя."""

    @circuit_breaker(fallback_function=fallback_exception_response, excluded_exceptions=(PyJWTError,))
    @jwt_required(fresh=True)
    @http_exceptions_handler()
    @rate_limit_requests(tat_storage=tat_storage, limit_requests=100, period=timedelta(seconds=60))
    def get(self, user_id: UUID) -> tuple[list[RoleSchema] | BaseResponseSchema, HTTPStatus]:
        """
        Метод, который предоставляет список всех ролей пользователя.

        Returns:
            список словарей, статус-код.
        """
        result = get_user_roles(user_id)

        if not result:
            return base_schema.dump(dict(
                msg='У пользователя нет ролей',
             )), HTTPStatus.NOT_FOUND

        return result, HTTPStatus.OK

    @circuit_breaker(fallback_function=fallback_exception_response, excluded_exceptions=(PyJWTError,))
    @jwt_required(fresh=True)
    @http_exceptions_handler()
    @rate_limit_requests(tat_storage=tat_storage, limit_requests=100, period=timedelta(seconds=60))
    @admin_required
    def post(self, user_id: UUID) -> tuple[str | dict, HTTPStatus]:
        """
        Метод, который добавляет роли пользователю.

        Returns:
            идентификаторы ролей, статус-код.
        """
        request_body = get_request_params(
            ParserParam('roles', dict(type=str, location='json', action='append')),
        )

        role_names = request_body.get('roles')

        transaction(add_roles_to_user, user_id, role_names)

        return base_schema.dump(dict(
            msg='Роли были добавлены пользователю',
        )), HTTPStatus.OK

    @circuit_breaker(fallback_function=fallback_exception_response, excluded_exceptions=(PyJWTError,))
    @jwt_required(fresh=True)
    @http_exceptions_handler()
    @rate_limit_requests(tat_storage=tat_storage, limit_requests=100, period=timedelta(seconds=60))
    @admin_required
    def delete(self, user_id: UUID) -> tuple[BaseResponseSchema, HTTPStatus]:
        """
        Метод удаляет у заданного пользователя роли из заданного списка ролей.
        Args:
            user_id: идентификатор пользователя

        Returns:
            статус-код
        """
        request_body = get_request_params(
            ParserParam('roles', dict(type=str, location='args', action='append')),
        )

        roles = request_body.get('roles')

        transaction(delete_roles_from_user, user_id, roles)

        return base_schema.dump(dict(
            msg='Роли были удалены для пользователя.',
        )), HTTPStatus.OK


class InfoUsers(Resource):
    """Класс предоставляющий доступ к персональной информации о пользователях."""

    @circuit_breaker(fallback_function=fallback_exception_response, excluded_exceptions=(PyJWTError,))
    @jwt_required()
    @http_exceptions_handler()
    @rate_limit_requests(tat_storage=tat_storage, limit_requests=100, period=timedelta(seconds=60))
    @admin_required
    def get(self) -> dict:
        """
        Метод возвращает выборку пользователей по соотв. параметрам поиска.

        Returns:
            Постраничный вывод информации о пользователях
        """

        request_body = get_request_params(
            ParserParam(SearchInfoUserParams.USER_IDS.value, dict(type=str, location='args', action='append')),
            ParserParam(SearchInfoUserParams.USER_GROUPS.value, dict(type=str, location='args', action='append')),
            ParserParam(SearchInfoUserParams.PAGE_NUMBER.value, dict(type=page_type, location='args', required=True)),
            ParserParam(SearchInfoUserParams.LIMIT.value, dict(type=limit_type, location='args', required=True))
        )
        infos = InfoUsersList(request_body)
        return infos.get()


api.add_resource(
    UserRolesListAPI,
    '/<uuid:user_id>/roles/',
    '/<uuid:user_id>/roles/create',
    '/<uuid:user_id>/roles/delete',
)
api.add_resource(InfoUsers, '/user-infos')
