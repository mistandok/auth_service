"""Модуль содержит в себе фикстуры, помогающие в реализации тестов."""

import asyncio
import pytest_asyncio

pytest_plugins = (
    "tests.functional.fixtures.connections",
    "tests.functional.fixtures.data_work"
)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()
