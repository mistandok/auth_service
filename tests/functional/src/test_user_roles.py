"""Модкуль содержащий тесты ручек для ролей пользователей."""

from uuid import uuid4
import pytest

from tests.functional.utils.api import api_get_request
from tests.functional.testdata.roles import (
    get_test_user_data_denied,
    get_test_user_data_allowed,
    get_test_user_data_denied_incorrect,
    get_test_user_data_allowed_incorrect,
    get_test_user_data_denied_incorrect_add_role,
    get_test_user_data_denied_incorrect_del_role
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'user, expected_status',
    get_test_user_data_denied(),
)
async def test_adding_roles_to_user(
    db_connection,
    prepare_tokens,
    api_session,
    user,
    expected_status
):
    """Тест добавления ролей пользователю по id."""

    role_ids = [str(uuid4()), str(uuid4())]
    role_names = []
    for num, role_id in enumerate(role_ids):
        role_name = f'test_add_role_{num}_{user}'
        await db_connection.execute(f"""
            INSERT INTO auth.role
            (id, name, description)
            VALUES
            ('{role_id}', '{role_name}', 'test_add_role_{num}');
        """)
        role_names.append(role_name)
    query = {'roles': role_names}
    user_id = str(uuid4())
    await db_connection.execute(f"""
         INSERT INTO auth.user
         (id, login, email, password)
         VALUES
         ('{user_id}', 'test_add_role_{user}', 'test_add_role_{user}', 'test_add_role');
     """)
    url = f'/auth/api/v1/users/{user_id}/roles/'

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
    get_test_user_data_allowed(),
)
async def test_get_user_roles(
    db_connection,
    prepare_tokens,
    api_session,
    user,
    expected_status
):
    """Тест предоставления ролей пользователя по id."""

    expected_body = []
    role_ids = [str(uuid4()), str(uuid4())]
    for num, role_id in enumerate(role_ids):
        role_name = f'test_get_user_roles_{num}_{user}'
        await db_connection.execute(f"""
            INSERT INTO auth.role
            (id, name, description)
            VALUES
            ('{role_id}', '{role_name}', 'test_get_user_roles_{num}');
        """)
        expected_body.append({'id': role_id, 'name': role_name})
    user_id = str(uuid4())
    await db_connection.execute(f"""
         INSERT INTO auth.user
         (id, login, email, password)
         VALUES
         ('{user_id}', 'test_get_user_roles_{user}', 'test_get_user_roles_{user}', 'test_get_user_roles');
     """)
    for role_id in role_ids:
        await db_connection.execute(f"""
             INSERT INTO auth.user_role
             (id, user_id, role_id)
             VALUES
             ('{str(uuid4())}', '{user_id}', '{role_id}');
         """)
    url = f'/auth/api/v1/users/{user_id}/roles/create'

    body, headers, status = await api_get_request(
        api_session,
        'GET',
        url,
        token=prepare_tokens.get(user).get('access_token')
    )

    assert body == expected_body
    assert status == expected_status


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'user, expected_status',
    get_test_user_data_denied(),
)
async def test_delete_user_roles(
    db_connection,
    prepare_tokens,
    api_session,
    user,
    expected_status
):
    """Тест удаления ролей пользователя по id."""

    role_ids = [str(uuid4()), str(uuid4())]
    role_names = []
    for num, role_id in enumerate(role_ids):
        role_name = f'test_del_user_roles_{num}_{user}'
        await db_connection.execute(f"""
            INSERT INTO auth.role
            (id, name, description)
            VALUES
            ('{role_id}', '{role_name}', 'test_del_user_roles_{num}');
        """)
        role_names.append(role_name)
    query = {'roles': role_names}
    user_id = str(uuid4())
    await db_connection.execute(f"""
         INSERT INTO auth.user
         (id, login, email, password)
         VALUES
         ('{user_id}', 'test_del_user_roles_{user}', 'test_del_user_roles_{user}', 'test_del_user_roles');
     """)
    for role_id in role_ids:
        await db_connection.execute(f"""
             INSERT INTO auth.user_role
             (id, user_id, role_id)
             VALUES
             ('{str(uuid4())}', '{user_id}', '{role_id}');
         """)

    url = f'/auth/api/v1/users/{user_id}/roles/delete'

    body, headers, status = await api_get_request(
        api_session,
        'DELETE',
        url,
        params=query,
        token=prepare_tokens.get(user).get('access_token')
    )

    assert status == expected_status


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'user, expected_status',
    get_test_user_data_allowed_incorrect(),
)
async def test_get_incorrect_user_roles(
    prepare_tokens,
    api_session,
    user,
    expected_status
):
    """Тест добавления ролей пользователю по некорректному id."""

    some_id = str(uuid4())
    url = f'/auth/api/v1/users/{some_id}/roles/create'

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
    get_test_user_data_denied_incorrect_del_role(),
)
async def test_delete_incorrect_users_roles(
    prepare_tokens,
    api_session,
    user,
    expected_status
):
    """Тест удаления ролей пользователя по некорректному id."""

    query = {'roles': ['some_role_name_1', 'some_role_name_2']}
    some_id = str(uuid4())
    url = f'/auth/api/v1/users/{some_id}/roles/delete'

    body, headers, status = await api_get_request(
        api_session,
        'DELETE',
        url,
        params=query,
        token=prepare_tokens.get(user).get('access_token')
    )

    assert status == expected_status


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'user, expected_status',
    get_test_user_data_denied_incorrect_add_role(),
)
async def test_adding_roles_to_incorrect_user(
    db_connection,
    prepare_tokens,
    api_session,
    user,
    expected_status
):
    """Тест добавления ролей пользователю по некорректному id."""

    role_ids = [str(uuid4()), str(uuid4())]
    role_names = []
    for num, role_id in enumerate(role_ids):
        role_name = f'test_inc_add_role_{num}_{user}'
        await db_connection.execute(f"""
            INSERT INTO auth.role
            (id, name, description)
            VALUES
            ('{role_id}', '{role_name}', 'test_inc_add_role{num}');
        """)
        role_names.append(role_name)
    query = {'roles': role_names}
    some_id = str(uuid4())
    url = f'/auth/api/v1/users/{some_id}/roles/'

    body, headers, status = await api_get_request(
        api_session,
        'POST',
        url,
        json=query,
        token=prepare_tokens.get(user).get('access_token')
    )

    assert status == expected_status
