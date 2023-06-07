"""Модуль тестирования аутентификации пользователя."""

from http import HTTPStatus

import pytest

from tests.functional.utils.api import api_get_request


@pytest.mark.asyncio
async def test_login_exists_user(
        api_session
):
    """Тест проверяет логин существующего пользователя."""
    url = '/auth/api/v1/account/login'
    datas = {
        'login': 'test_user',
        'password': 'test_pwd'
    }

    body, _, status = await api_get_request(
        api_session,
        'POST',
        url,
        json=datas
    )

    assert status == HTTPStatus.OK


@pytest.mark.asyncio
async def test_history(
        prepare_tokens,
        api_session
):
    """Тест проверяет историю устройств по заданному лимиту."""
    params = {
        'limit': 2
    }
    url = '/auth/api/v1/account/history-auth'

    body, _, status = await api_get_request(
        api_session,
        'GET',
        url,
        json=params,
        token=prepare_tokens.get('admin').get('access_token'),
    )
    assert len(body.get('result')) <= 2


@pytest.mark.asyncio
async def test_signup_exists_user(
        api_session
):
    """Тест проверяет регистрацию существующего пользователя."""
    url = '/auth/api/v1/account/signup'
    datas = {
        'login': 'test_user',
        'email': 'test_email',
        'password': 'test_pwd'
    }

    body, _, status = await api_get_request(
        api_session,
        'POST',
        url,
        json=datas
    )

    assert status == HTTPStatus.CONFLICT


@pytest.mark.asyncio
async def test_wrong_pwd(
        api_session
):
    """Тест проверяет логин по неверному паролю."""
    url = '/auth/api/v1/account/login'
    datas = {
        'login': 'test_user',
        'password': 'test_pwd1'
    }

    body, _, status = await api_get_request(
        api_session,
        'POST',
        url,
        json=datas
    )

    assert status == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_refresh(
        api_session
):
    """Тест проверяет смену токена."""
    datas = {
        'login': 'user1',
        'email': 'user1',
        'password': 'user1'
    }
    await api_get_request(
        api_session,
        'POST',
        '/auth/api/v1/account/signup',
        json=datas
    )
    del datas['email']

    body, _, _ = await api_get_request(
        api_session,
        'POST',
        '/auth/api/v1/account/login',
        json=datas
    )

    _, _, status = await api_get_request(
        api_session,
        'GET',
        '/auth/api/v1/account/refresh',
        token=body.get('refresh_token')
    )

    assert status == HTTPStatus.OK


@pytest.mark.asyncio
async def test_logout(
        api_session
):
    """Тест проверяет логаут."""
    datas = {
        'login': 'user2',
        'email': 'user2',
        'password': 'user2'
    }
    await api_get_request(
        api_session,
        'POST',
        '/auth/api/v1/account/signup',
        json=datas
    )
    del datas['email']

    body, _, _ = await api_get_request(
        api_session,
        'POST',
        '/auth/api/v1/account/login',
        json=datas
    )
    token = body.get('access_token')

    await api_get_request(
        api_session,
        'DELETE',
        '/auth/api/v1/account/logout',
        token=token
    )

    _, _, status = await api_get_request(
        api_session,
        'GET',
        '/auth/api/v1/account/history-auth',
        token=token
    )

    assert status == HTTPStatus.UNAUTHORIZED
