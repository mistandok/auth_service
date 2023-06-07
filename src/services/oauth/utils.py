"""Модуль с набором утилит для работы с OAuth."""
from sqlalchemy import select

from db import db_session
from db_models import User, OAuthUser


def generate_access_token_key_to_oauth_user(provider: str, client_id_user: str) -> str:
    """Метод генерирует ключ для `access` токена для `client_id` конкретного провайдера"""
    return f'{provider}_{client_id_user}_access'


def generate_refresh_token_key_to_oauth_user(provider: str, client_id_user: str) -> str:
    """Метод генерирует ключ для `refresh` токена для `client_id` конкретного провайдера"""
    return f'{provider}_{client_id_user}_refresh'


def get_user_by_oauth_user(client_id: str) -> User | None:
    """
    Метод проверят сущ. пользователя в таблице `oauth_user` по `client_id`.

    Returns:
        User | None
    """

    query = (
        select(User)
        .join(OAuthUser)
        .where(OAuthUser.columns.client_id == str(client_id))
    )

    result = db_session.execute(query)
    return result.scalar_one_or_none()
