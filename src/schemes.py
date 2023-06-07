from marshmallow import Schema

from db_models import User, Role, UserAuthHistory, Scope, Permissions


class UserSchema(Schema):
    """Класс сериализующий модель `User`."""

    class Meta:
        fields = (
            'id',
            'email',
            'first_name',
            'surname',
            'patronymic',
            'login',
            'phone',
            'created_at'
        )
        model = User


class RoleSchema(Schema):
    """Класс сериализующий модель `Role`."""

    class Meta:
        fields = ('id', 'name', 'description')
        model = Role


class UserAuthHistorySchema(Schema):
    """Класс сериализующий модель `UserAuthHistory`."""

    class Meta:
        fields = ('user_id', 'user_agent', 'device_type', 'created_at', 'id')
        model = UserAuthHistory


class ScopeSchema(Schema):
    """Класс сериализующий модель `Scope`."""

    class Meta:
        fields = ('id', 'name', 'created_at')
        model = Scope


class PermissionsSchema(Schema):
    """Класс сериализующий модель `Permissions`."""

    class Meta:
        fields = ('id', 'scope_id', 'role_id', 'access_level', 'created_at', 'updated_at')
        model = Permissions


class PermissionsResponseSchema(Schema):
    """Класс сериализует успешный ответ сервиса на запрос разрешений."""

    class Meta:
        fields = ('admin', 'write', 'read')


class TokensSchema(Schema):
    """Класс сериализуюет Токены."""

    class Meta:
        fields = ('access_token', 'refresh_token')


class AccessTokenSchema(Schema):
    """Класс сериализует access-токен"""

    class Meta:
        fields = ('access_token',)


class BaseResponseSchema(Schema):
    """Класс сериализует успешный ответ сервиса"""

    class Meta:
        fields = ('msg',)


class ListResponseSchema(Schema):

    class Meta:
        fields = ('result', 'outcome')


class OAuthTokensSchema(Schema):

    class Meta:
        fields = ('access_token', 'refresh_token', 'message')


user_schema = UserSchema()
users_schema = UserSchema(many=True)
auth_histories_schema = UserAuthHistorySchema(many=True)
scope_schema = ScopeSchema()
permission_schema = PermissionsSchema()
permission_response_schema = PermissionsResponseSchema()
tokens_schema = TokensSchema()
access_token_schema = AccessTokenSchema()
base_schema = BaseResponseSchema()

role_schema = RoleSchema()
roles_schema = RoleSchema(many=True)

list_response_schema = ListResponseSchema()

oauth_tokens_schema = OAuthTokensSchema()
