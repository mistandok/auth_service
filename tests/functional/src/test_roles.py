"""Модкуль содержащий тесты ручек для ролей."""
from uuid import uuid4
import pytest

from tests.functional.utils.api import api_get_request
from tests.functional.testdata.roles import (
    get_test_user_data_denied,
    get_test_user_data_denied_incorrect
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'user, expected_status',
    get_test_user_data_denied(),
)
async def test_create_role(
    prepare_tokens,
    api_session,
    user,
    expected_status
):
    """Тест создания роли."""

    query = {'name': f'test_create_role_{user}', 'description': 'test_create_role'}
    url = '/auth/api/v1/role/create'

    body, headers, status = await api_get_request(
        api_session,
        'POST',
        url,
        json=query,
        token=prepare_tokens.get(user).get('access_token')
    )

    assert status == expected_status


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'user, expected_status',
    get_test_user_data_denied(),
)
async def test_get_role(
    db_connection,
    prepare_tokens,
    api_session,
    user,
    expected_status
):
    """Тест предоставления роли по id."""

    role_id = await db_connection.fetchval("SELECT id FROM auth.role WHERE name = 'admin';")
    url = f'/auth/api/v1/role/{str(role_id)}'

    body, headers, status = await api_get_request(
        api_session,
        'GET',
        url,
        token=prepare_tokens.get(user).get('access_token')
    )

    assert status == expected_status


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'user, expected_status',
    get_test_user_data_denied(),
)
async def test_update_role(
    db_connection,
    prepare_tokens,
    api_session,
    user,
    expected_status
):
    """Тест обновления параметров роли по id."""

    role_id = str(uuid4())
    await db_connection.fetchval(f"""
            INSERT INTO auth.role
            (id, name, description)
            VALUES
            ('{role_id}', 'test_update_role_{user}', 'test_update_role');
    """)

    query = {'name': f'test_role_updated_{user}', 'description': 'test_role_updated'}
    url = f'/auth/api/v1/role/{str(role_id)}/update'

    body, headers, status = await api_get_request(
        api_session,
        'PATCH',
        url,
        json=query,
        token=prepare_tokens.get(user).get('access_token')
    )

    assert status == expected_status


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'user, expected_status',
    get_test_user_data_denied(),
)
async def test_delete_role(
    db_connection,
    prepare_tokens,
    api_session,
    user,
    expected_status
):
    """Тест удаления роли по id."""

    role_id = str(uuid4())
    await db_connection.fetchval(f"""
            INSERT INTO auth.role
            (id, name, description)
            VALUES
            ('{role_id}', 'test_delete_role_{user}', 'test_delete_role');
    """)
    url = f'/auth/api/v1/role/{role_id}/delete'

    body, headers, status = await api_get_request(
        api_session,
        'DELETE',
        url,
        token=prepare_tokens.get(user).get('access_token')
    )

    assert status == expected_status


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'user, expected_status',
    get_test_user_data_denied(),
)
async def test_get_roles(
    prepare_tokens,
    api_session,
    user,
    expected_status
):
    """Тест предоставления всех ролей."""

    url = '/auth/api/v1/roles'

    body, headers, status = await api_get_request(
        api_session,
        'GET',
        url,
        token=prepare_tokens.get(user).get('access_token')
    )

    assert status == expected_status


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'user, expected_status',
    get_test_user_data_denied_incorrect(),
)
async def test_get_incorrect_role(
    prepare_tokens,
    api_session,
    user,
    expected_status
):
    """Тест предоставления роли по некорректному id."""

    some_id = str(uuid4())
    url = f'/auth/api/v1/role/{str(some_id)}'

    body, headers, status = await api_get_request(
        api_session,
        'GET',
        url,
        token=prepare_tokens.get(user).get('access_token')
    )

    assert status == expected_status


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'user, expected_status',
    get_test_user_data_denied_incorrect(),
)
async def test_update_incorrect_role(
    prepare_tokens,
    api_session,
    user,
    expected_status
):
    """Тест обновления параметров роли по некорректному id."""

    some_id = str(uuid4())
    query = {'name': f'test_inc_role_updated_{user}', 'description': 'test_inc_role_updated'}
    url = f'/auth/api/v1//role/{str(some_id)}/update'

    body, headers, status = await api_get_request(
        api_session,
        'PATCH',
        url,
        json=query,
        token=prepare_tokens.get(user).get('access_token')
    )

    assert status == expected_status


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'user, expected_status',
    get_test_user_data_denied_incorrect(),
)
async def test_delete_incorrect_role(

    prepare_tokens,
    api_session,
    user,
    expected_status
):
    """Тест удаления роли по некорректному id."""

    some_id = str(uuid4())
    url = f'/auth/api/v1/role/{some_id}/delete'

    body, headers, status = await api_get_request(
        api_session,
        'DELETE',
        url,
        token=prepare_tokens.get(user).get('access_token')
    )

    assert status == expected_status
