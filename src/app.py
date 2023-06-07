"""Основной модуль для старта приложения."""
from gevent import monkey

monkey.patch_all()

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_restful import Api

from api.v1.account import account_blueprint
from api.v1.oauth import oauth_blueprint
from api.v1.roles import role_blueprint, roles_blueprint
from api.v1.users import users_blueprint
from api.v1.permissions import user_permissions_blueprint
from db import blocklist
from core.config import JWT_SETTINGS, APP_SETTINGS
from services.utils import create_admin_user, create_roles, exclude_for_test

from gevent.pywsgi import WSGIServer

from opentelemetry.instrumentation.flask import FlaskInstrumentor

from services.jaeger.tracer import configure_tracer, setup_tracer


exclude_for_test(configure_tracer)()
app = Flask(__name__)

exclude_for_test(FlaskInstrumentor().instrument_app)(app)


@app.before_request
def before_request():
    """Метод проверяет полученные запросы."""
    exclude_for_test(setup_tracer)()


app.config['JWT_ACCESS_TOKEN_EXPIRES'] = JWT_SETTINGS.access_token_expires
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = JWT_SETTINGS.refresh_token_expires
app.config['JWT_SECRET_KEY'] = JWT_SETTINGS.secret_key.encode('utf-8')

api = Api(app, errors=Flask.errorhandler)
jwt = JWTManager(app)


@jwt.token_in_blocklist_loader
def is_token_revoked(jwt_header, jwt_payload: dict) -> bool:
    """
    Функция проверяет, что токен находится в блок-листе.

    В аксесс токене хранится ID рефреш-токена.
    Это сделано для того, чтобы иметь возможность осуществить логаут со всех устройств:
    при логауте со всех устройств, или с определенных устройств,
    рефреш токены добавляются в блоклист, соответственно все аксесс токены, которые
    на них ссылаются, тоже становятся недоступны.

    Args:
        jwt_header: заголовок токена.
        jwt_payload: тело токена.

    Returns:
        bool: True - в блок-листе, False - токен не в блок-листе.
    """
    jti = jwt_payload.get('jti')
    is_token_in_blocklist = blocklist.get(jti) is not None

    refresh_jti = jwt_payload.get('sub', {}).get('refresh_jti')
    is_refresh_token_in_blocklist = blocklist.get(refresh_jti) is not None if refresh_jti else False

    return is_token_in_blocklist or is_refresh_token_in_blocklist


app.register_blueprint(role_blueprint, url_prefix=f'{APP_SETTINGS.api_prefix_v1}/role')
app.register_blueprint(roles_blueprint, url_prefix=f'{APP_SETTINGS.api_prefix_v1}/roles')
app.register_blueprint(users_blueprint, url_prefix=f'{APP_SETTINGS.api_prefix_v1}/users')
app.register_blueprint(account_blueprint, url_prefix=f'{APP_SETTINGS.api_prefix_v1}/account')
app.register_blueprint(user_permissions_blueprint, url_prefix=f'{APP_SETTINGS.api_prefix_v1}/user-permissions')
app.register_blueprint(oauth_blueprint, url_prefix=f'{APP_SETTINGS.api_prefix_v1}/oauth')


if __name__ == '__main__':
    create_admin_user()
    create_roles()
    # create_scopes()
    # create_permissions()

    if APP_SETTINGS.debug.lower() == 'true':
        app.run(host=APP_SETTINGS.host, port=APP_SETTINGS.port)
    else:
        http_server = WSGIServer((APP_SETTINGS.host, APP_SETTINGS.port), app)
        http_server.serve_forever()
