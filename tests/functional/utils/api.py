"""Объекты для работы с API."""

import aiohttp
import backoff
from aiohttp import ClientSession


@backoff.on_exception(
    backoff.expo,
    (
        ConnectionRefusedError,
        aiohttp.client.ClientConnectorError,
        aiohttp.client.ClientError,
    ),
)
async def api_get_request(
        api_session: ClientSession,
        request_method: str,
        url: str,
        params: dict | None = None,
        json: dict | None = None,
        token: str | None = None
):
    """Функция отвечает за get запросы к API.

    Args:
        api_session: экзепляр клиентской сессии.
        request_method: метод запроса.
        url: url-адрес API.
        json: параметры запроса к API в параметрах запроса.
            Параметры со значением None фильтруются и не участвуют в запросе.
        params: параметры запроса к API в теле запроса.
            Параметры со значением None фильтруются и не участвуют в запросе.
        token: токен пользователя.
    """
    if params:
        params = {key: value for key, value in params.items() if value is not None}
    if json:
        json = {key: value for key, value in json.items() if value is not None}

    if token:
        api_session.headers.update({'Authorization': f'Bearer {token}'})

    async with api_session.request(
            request_method,
            url,
            params=params,
            json=json
    ) as response:
        body = await response.json()
        headers = response.headers
        status = response.status

    return body, headers, status
