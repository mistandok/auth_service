"""Моуль отвечает за идентификацию, аутентификацию и авторизацию."""
import uuid
from http import HTTPStatus

from flask_jwt_extended import create_refresh_token, decode_token, create_access_token
from sqlalchemy.exc import IntegrityError

from core.config import JWT_SETTINGS, DB_SETTINGS
from db import refresh_list, blocklist, db_session
from db_models import User
from services.storages.key_value.utils import generate_key
from services.user.utils import is_user_exists, create_user, get_user_by_login, update_user, add_roles_to_user
from services.role.utils import get_user_roles
from services.permissions.config import RoleName
from services.passwords.utils import get_hash_password, is_correct_password
from services.http_exceptions.auth_exceptions import IncorrectPassword
from services.http_exceptions.common_exceptions import MissingUpdatedData, MissingEntity, DuplicatedEntity
from services.user_history.utils import create_user_history
from services.logs import logs

logger = logs.get_logger()


def sign_up(user: User):
    """
    Функция отвечает за регистрацию пользователя в системе.

    В случае отсутствия пользователя в системе функция создает пользователя и сохраняет с захэшированным паролем.
    ВНИМАНИЕ: пароль переданного пользователя в этой функции будет хэшироваться.

    Args:
        user: модель пользователя.
        unhashed_password: пароль пользователя.

    Raises:
        DuplicateAuthData
    """
    logger.info('Регистрация пользователя login: %s, email: %s', user.login, user.email)

    is_email_exists, is_login_exists = is_user_exists(email=user.email, login=user.login)

    err_msg = {
        (True, True): f'Пользователь с {user.email=} и {user.login=} уже существует!',
        (True, False): f'Пользователь с {user.email=} уже существует!',
        (False, True): f'Пользователь с {user.login=} уже существует!'
    }.get((is_email_exists, is_login_exists))

    if err_msg:
        raise DuplicatedEntity(err_msg, HTTPStatus.CONFLICT)

    user.password = get_hash_password(user.password)
    user.id = uuid.uuid4()

    create_user(user)
    db_session.commit()

    add_roles_to_user(user.id, [RoleName.USER.value])


def login(user_login: str, user_password: str, user_agent: str) -> tuple[str, str]:
    """
    Функция осуществляет вход пользователя в систему.

    Args:
        user_login: логин пользователя.
        user_password: пароль пользователя.
        user_agent: информация об устройстве, с которого был осуществлен вход.

    Returns:
        tuple[str, str]: access_token, refresh_token

    Raises:
        MissUser
        IncorrectPassword
    """
    logger.info('LogIn пользователя login: %s, user_agent: %s', user_login, user_agent)

    user = get_user_by_login(user_login)

    if not user:
        raise MissingEntity(f'Пользозвателя {user_login=} не существует, зарегистрируйтесь!', HTTPStatus.NOT_FOUND)

    if not is_correct_password(user_password, user.password):
        raise IncorrectPassword('Введен некорректный пароль!', HTTPStatus.UNAUTHORIZED)

    create_user_history(user, user_agent)

    user_roles = [user_role.get('name') for user_role in get_user_roles(user.id)]

    access_token, refresh_token = create_tokens(user.id, user_agent, user_roles, user.email)

    return access_token, refresh_token


def create_tokens(user_id: uuid.UUID, user_agent: str, user_roles: list, user_email: str):
    """
    Функция создаёт access и refresh токены с параметрами и возвращает их.

    Args:
        user_id: идентификатор пользователя.
        user_agent: информация об устройстве, с которого был осуществлен вход.
        user_roles: роли пользователя.
        user_email: email пользователя

    Returns:
        tuple[str, str]: access_token, refresh_token
    """

    refresh_identity = dict(
        user_id=user_id,
        user_agent=user_agent
    )
    refresh_token = create_refresh_token(identity=refresh_identity)
    decoded_refresh_token = decode_token(refresh_token)

    refresh_list_key = generate_key(user_id, user_agent)
    refresh_list.put(refresh_list_key, refresh_token, expire=JWT_SETTINGS.refresh_token_expires)

    access_identity = dict(
        user_id=user_id,
        user_roles=user_roles,
        user_agent=user_agent,
        email=user_email,
        refresh_jti=decoded_refresh_token.get('jti')
    )
    access_token_params = dict(
        identity=access_identity,
        fresh=True,
        expires_delta=False if DB_SETTINGS.admin in user_roles else None
    )
    access_token = create_access_token(**access_token_params)

    return access_token, refresh_token


def logout(access_token_payload: dict):
    """
    Функция добавляет в блоклист акксесс и рефреш токены при логауте.

    Args:
        access_token_payload: тело access-токена.
    """
    access_jti = access_token_payload.get('jti')
    refresh_jti = access_token_payload.get('sub', {}).get('refresh_jti')

    blocklist.put(access_jti, '', expire=JWT_SETTINGS.access_token_expires)
    blocklist.put(refresh_jti, '', expire=JWT_SETTINGS.refresh_token_expires)


def refresh(refresh_token_payload: dict, refresh_identity: dict) -> str:
    """
    Функция рефрешит сессию пользователя и возвращает новый access токен.

    Args:
        refresh_token_payload: тело refresh-токена.
        refresh_identity: основная информация по refresh-токену.

    Returns:
        access-токен.
    """
    user_roles = [
        user_role.get('name') for user_role in get_user_roles(refresh_token_payload.get('sub').get('user_id'))
    ]

    access_identity = refresh_identity.copy()
    access_identity.update(
        dict(
            refresh_jti=refresh_token_payload.get('jti'),
            user_roles=user_roles
        )
    )
    access_token = create_access_token(access_identity, fresh=True)
    return access_token


def update_auth_data(user_id: uuid, new_login: str | None = None, new_password: str | None = None):
    """
    Функция осуществляет обновление аутентификационных данных пользователя по переданным параметрам.

    ВНИМАНИЕ! Функция хэширует полученное значение пароля.

    Args:
        user_id: ID юзера.
        new_login: новый логин.
        new_password: новый пароль.
    """
    logger.info('Обновление аутентификационных данных для пользователя user_id: %s, user_agent: %s', user_id)

    if not new_login and not new_password:
        raise MissingUpdatedData('Не переданы данные для обновления', HTTPStatus.BAD_REQUEST)

    new_values = {}
    if new_password:
        new_values['password'] = get_hash_password(new_password)
    if new_login:
        new_values['login'] = new_login

    try:
        update_user(user_id, new_values)
    except IntegrityError:
        logger.warning(
            'Ошибка обновления auth-данных, user_id: %s, new_login: $s',
            user_id,
            new_login,
            exc_info=True,
        )
        raise DuplicatedEntity('Пользователь с таким логином уже существует.', HTTPStatus.CONFLICT)


def logout_user_for_user_agents(user_id: uuid, user_agents: list[str]):
    """
    Функция осуществляет логаут для указанных устройств.

    Если в параметре 'user_agents' будет передано значение ['all'],
    то произойдет логаут всех активных сессий. Иначе пройдем по списку сессий и выйдем только из тех, которые
    в нем указаны.

    Args:
        user_id: ID пользователя.
        user_agents: устройства юзера для отключения.
    """
    logger.info(
        'Логаут пользователя user_id: %s с устройств %s',
        user_id,
        user_agents,
    )

    if len(user_agents) == 1 and 'all' in user_agents:
        for refresh_list_id, refresh_token in refresh_list.get_by_template(f'*{user_id}*'):
            if refresh_token:
                _logout_by_refresh_token(refresh_list_id, refresh_token)
    else:
        for user_agent in user_agents:
            refresh_list_id = generate_key(user_id, user_agent)
            refresh_token = refresh_list.get(refresh_list_id)
            if refresh_token:
                _logout_by_refresh_token(refresh_list_id, refresh_token)


def _logout_by_refresh_token(refresh_list_id: str, refresh_token):
    """
    Служебная функция. Осуществляет логаут для пользователя по его рефреш токену.

    Добавляет рефреш токен в блоклист и удаляет его из доступных рефреш токенов.
    Args:
        refresh_list_id: ID токена в списке рефреш токенов (refresh_list)
        refresh_token: закодированный токен
    """
    decoded_refresh_token = decode_token(refresh_token)
    refresh_jti = decoded_refresh_token.get('jti')
    blocklist.put(refresh_jti, '', expire=JWT_SETTINGS.refresh_token_expires)
    refresh_list.delete(refresh_list_id)
