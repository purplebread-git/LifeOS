"""Тесты Container проверяют ТОЛЬКО структуру графа зависимостей.

agent.respond() здесь не вызывается: Container теперь резолвит настоящий
OpenAIProvider, а вызов respond() означал бы реальный сетевой запрос к
OpenAI API. Поведение Agent/ConversationEngine проверяется отдельно в
test_agent.py с фейковым LLMProvider.
"""

from collections.abc import AsyncGenerator
from os import environ

import pytest_asyncio

from app.config.settings import get_settings
from app.container import Container
from app.context import LayeredContextBuilder
from app.core.agent import Agent
from app.core.context_builder import ContextBuilder
from app.core.conversation_engine import ConversationEngine
from app.core.conversation_repository import ConversationRepository
from app.core.knowledge_provider import KnowledgeProvider
from app.core.llm_provider import LLMProvider
from app.core.memory_provider import MemoryProvider
from app.core.plugin_registry import PluginRegistry
from app.knowledge.document_ingestion_service import DocumentIngestionService
from app.knowledge.sqlite_knowledge_provider import SqliteKnowledgeProvider
from app.memory.sqlite_memory_provider import SqliteMemoryProvider
from app.providers.openai import OpenAIProvider


@pytest_asyncio.fixture
async def container() -> AsyncGenerator[Container, None]:
    environ["OPENAI_API_KEY"] = "test-key"
    # In-memory SQLite: тест проверяет реальный persistent-бэкенд через DI,
    # но без создания файла на диске.
    environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

    get_settings.cache_clear()

    c = Container()

    init_result = c.init_resources()
    if init_result is not None:
        await init_result

    yield c

    shutdown_result = c.shutdown_resources()
    if shutdown_result is not None:
        await shutdown_result

    get_settings.cache_clear()


# agent / conversation_engine / memory_provider транзитивно зависят от
# async-ресурса database, поэтому их резолв возвращает awaitable.


async def test_container_resolves_agent(container: Container) -> None:
    # dependency-injector типизирует резолв синхронно, но из-за async-ресурса
    # database фактически возвращается awaitable — отсюда type: ignore.
    assert isinstance(await container.agent(), Agent)  # type: ignore[misc]


async def test_container_resolves_conversation_engine(container: Container) -> None:
    assert isinstance(await container.conversation_engine(), ConversationEngine)  # type: ignore[misc]


async def test_container_resolves_conversation_repository(container: Container) -> None:
    assert isinstance(container.conversation_repository(), ConversationRepository)


async def test_container_resolves_memory_provider_as_sqlite(container: Container) -> None:
    provider = await container.memory_provider()
    assert isinstance(provider, SqliteMemoryProvider)
    assert isinstance(provider, MemoryProvider)


async def test_container_resolves_knowledge_provider_as_sqlite(container: Container) -> None:
    provider = await container.knowledge_provider()
    assert isinstance(provider, SqliteKnowledgeProvider)
    assert isinstance(provider, KnowledgeProvider)


async def test_container_resolves_document_ingestion_service(container: Container) -> None:
    service = await container.document_ingestion_service()  # type: ignore[misc]
    assert isinstance(service, DocumentIngestionService)


async def test_container_resolves_context_builder_as_layered(container: Container) -> None:
    builder = await container.context_builder()  # type: ignore[misc]
    assert isinstance(builder, LayeredContextBuilder)
    assert isinstance(builder, ContextBuilder)


async def test_container_resolves_llm_provider_as_openai(container: Container) -> None:
    assert isinstance(container.llm_provider(), OpenAIProvider)
    assert isinstance(container.llm_provider(), LLMProvider)


async def test_plugin_lifecycle_resolves_with_default_plugins(
    container: Container,
) -> None:
    manager = await container.plugin_manager()  # type: ignore[misc]
    registry = container.plugin_registry()

    assert manager is not None
    assert isinstance(registry, PluginRegistry)
    # Composition root подключает EchoPlugin — registry не пуст.
    assert "echo" in [tool.definition.name for tool in registry.all_registered_tools()]
