"""Модуль содержит в себе API для работы с ролями."""
from datetime import timedelta
from http import HTTPStatus
from uuid import UUID

from flask import Blueprint, Flask
from flask_restful import Resource, Api
from flask_jwt_extended import jwt_required
from jwt import PyJWTError
from sqlalchemy.exc import IntegrityError

from db import transaction, tat_storage
from db_models import Role
from schemes import role_schema, base_schema, BaseResponseSchema, RoleSchema, ListResponseSchema
from services.circuit_breaker.circuit import circuit_breaker
from services.http_exceptions.decorators import http_exceptions_handler
from services.rate_limit.gcra import rate_limit_requests
from services.request_parser import get_request_params, ParserParam
from services.role.utils import (
    get_role_by_id, create_role, update_role,
    delete_role, get_role_list,
)
from services.user.decorators import admin_required
from services.utils import fallback_exception_response

role_blueprint = Blueprint('role', __name__)
roles_blueprint = Blueprint('roles', __name__)
api_role = Api(role_blueprint, errors=Flask.errorhandler)
api_roles = Api(roles_blueprint, errors=Flask.errorhandler)


class CRUDRole(Resource):
    """CRUD-класс для конкретной роли."""

    @circuit_breaker(fallback_function=fallback_exception_response, excluded_exceptions=(PyJWTError,))
    @jwt_required(fresh=True)
    @http_exceptions_handler()
    @rate_limit_requests(tat_storage=tat_storage, limit_requests=100, period=timedelta(seconds=60))
    @admin_required
    def get(self, role_id: UUID) -> tuple[RoleSchema | BaseResponseSchema, HTTPStatus]:
        """
        Метод, который получает роль по `id`.

        Args:
            role_id: идентификатор роли

        Returns:
            сериализованный объект, статус-код.
        """
        result = get_role_by_id(role_id)

        if not result:
            return base_schema.dump(dict(msg=f'Роль с {role_id=} не существует')), HTTPStatus.NOT_FOUND

        return role_schema.dump(result), HTTPStatus.OK

    @circuit_breaker(fallback_function=fallback_exception_response, excluded_exceptions=(PyJWTError,))
    @jwt_required(fresh=True)
    @http_exceptions_handler()
    @rate_limit_requests(tat_storage=tat_storage, limit_requests=100, period=timedelta(seconds=60))
    @admin_required
    def post(self) -> tuple[RoleSchema | BaseResponseSchema, HTTPStatus]:
        """
        Метод, который создаёт роль по параметрам
        и записывает всё в БД.

        Returns:
            сериализованный объект созданной роли
            статус-код (int)
        """
        request_body = get_request_params(
            ParserParam('name', dict(type=str, location='json', required=True)),
            ParserParam('description', dict(type=str, location='json')),
        )

        try:
            role = Role(**request_body)
            transaction(create_role, role)
        except IntegrityError:
            return base_schema.dump(dict(
                msg=f'Роль с таким именем {request_body.get("name")} уже существует'
            )), HTTPStatus.BAD_REQUEST

        return role_schema.dump(role), HTTPStatus.OK

    @circuit_breaker(fallback_function=fallback_exception_response, excluded_exceptions=(PyJWTError,))
    @jwt_required(fresh=True)
    @http_exceptions_handler()
    @rate_limit_requests(tat_storage=tat_storage, limit_requests=100, period=timedelta(seconds=60))
    @admin_required
    def patch(self, role_id: UUID) -> tuple[BaseResponseSchema, HTTPStatus]:
        """
        Метод, который обновляет роль по параметрам
        и записывает всё в БД.

        Returns:
            role_id (str): идентификатор роли
            статус-код (int)
        """
        request_body = get_request_params(
            ParserParam('name', dict(type=str, location='json')),
            ParserParam('description', dict(type=str, location='json')),
        )

        new_name = request_body.get('name')
        new_description = request_body.get('description')

        role_was_updated = transaction(update_role, role_id, new_name, new_description)

        if not role_was_updated:
            return base_schema.dump(dict(
                msg=f'Роль с {role_id=} отсутствует, обновлять нечего.'
            )), HTTPStatus.NOT_FOUND

        return base_schema.dump(dict(
                msg=f'Роль с {role_id=} обновлена.'
            )), HTTPStatus.OK

    @circuit_breaker(fallback_function=fallback_exception_response, excluded_exceptions=(PyJWTError,))
    @jwt_required(fresh=True)
    @http_exceptions_handler()
    @rate_limit_requests(tat_storage=tat_storage, limit_requests=100, period=timedelta(seconds=60))
    @admin_required
    def delete(self, role_id: UUID) -> tuple[BaseResponseSchema, HTTPStatus]:
        """
        Метод, который удаляет роль по `id`.

        Args:
            role_id: идентификатор роли.

        Returns:
            статус-код
        """
        role_was_deleted = transaction(delete_role, role_id)

        if not role_was_deleted:
            return base_schema.dump(dict(
                msg=f'Роль с {role_id=} отсутствует, удалять нечего.'
            )), HTTPStatus.NOT_FOUND

        return base_schema.dump(dict(
                msg=f'Роль с {role_id=} удалена.'
            )), HTTPStatus.OK


class CRUDRolesList(Resource):
    """CRUD-классов для списочных методов."""

    @circuit_breaker(fallback_function=fallback_exception_response, excluded_exceptions=(PyJWTError,))
    @jwt_required(fresh=True)
    @http_exceptions_handler()
    @rate_limit_requests(tat_storage=tat_storage, limit_requests=100, period=timedelta(seconds=60))
    @admin_required
    def get(self) -> tuple[ListResponseSchema, HTTPStatus]:
        """
        Метод, который предоставляет список всех ролей.

        Returns:
            список словарей, статус-код.
        """
        return get_role_list(), HTTPStatus.OK


api_role.add_resource(
    CRUDRole,
    '/create',
    '/<uuid:role_id>/delete',
    '/<uuid:role_id>/update',
    '/<uuid:role_id>',
)
api_roles.add_resource(CRUDRolesList, '/')
