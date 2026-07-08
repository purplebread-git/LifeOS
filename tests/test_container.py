"""Тесты Container проверяют ТОЛЬКО структуру графа зависимостей.

agent.respond() здесь не вызывается: Container теперь резолвит настоящий
OpenAIProvider, а вызов respond() означал бы реальный сетевой запрос к
OpenAI API. Поведение Agent/ConversationEngine проверяется отдельно в
test_agent.py с фейковым LLMProvider.
"""

import pytest_asyncio
from collections.abc import AsyncGenerator
from app.container import Container
from app.core.agent import Agent
from app.core.conversation_engine import ConversationEngine
from app.core.conversation_repository import ConversationRepository
from app.core.llm_provider import LLMProvider
from app.core.plugin_registry import PluginRegistry
from app.providers.openai import OpenAIProvider


@pytest_asyncio.fixture
async def container() -> AsyncGenerator[Container, None]:
    c = Container()
    init_result = c.init_resources()
    if init_result is not None:
        await init_result
    yield c
    shutdown_result = c.shutdown_resources()
    if shutdown_result is not None:
        await shutdown_result


async def test_container_resolves_agent(container: Container) -> None:
    assert isinstance(container.agent(), Agent)


async def test_container_resolves_conversation_engine(container: Container) -> None:
    assert isinstance(container.conversation_engine(), ConversationEngine)


async def test_container_resolves_conversation_repository(container: Container) -> None:
    assert isinstance(container.conversation_repository(), ConversationRepository)


async def test_container_resolves_llm_provider_as_openai(container: Container) -> None:
    assert isinstance(container.llm_provider(), OpenAIProvider)
    assert isinstance(container.llm_provider(), LLMProvider)


async def test_plugin_lifecycle_resolves_even_without_plugins(container: Container) -> None:
    manager = container.plugin_manager()
    registry = container.plugin_registry()

    assert manager is not None
    assert isinstance(registry, PluginRegistry)
    assert registry.all_registered_tools() == []
