"""Composition root приложения.

app/core/ НИКОГДА не импортирует dependency-injector — библиотека
используется исключительно здесь, на границе wiring'а.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from dependency_injector import containers, providers
from pydantic import SecretStr

from app.agent import (
    SimpleAgent,
    SimpleContextBuilder,
    ToolConversationEngine,
)
from app.config.settings import get_settings
from app.conversation.in_memory_repository import InMemoryConversationRepository
from app.core.plugin import Plugin
from app.memory.in_memory_provider import InMemoryMemoryProvider
from app.plugins.manager import SimplePluginManager
from app.plugins.registry import SimplePluginRegistry
from app.providers.openai import OpenAIClient, OpenAIProvider
from app.tools.simple_tool_manager import SimpleToolManager


def _unwrap_secret(secret: SecretStr) -> str:
    return secret.get_secret_value()


async def _init_plugin_manager(
    plugins: list[Plugin],
    registry: SimplePluginRegistry,
) -> AsyncIterator[SimplePluginManager]:
    manager = SimplePluginManager(plugins=plugins, registry=registry)
    await manager.start()
    try:
        yield manager
    finally:
        await manager.stop()


class Container(containers.DeclarativeContainer):
    """Граф зависимостей приложения.

    Lifetimes:
      - Singleton: OpenAIClient, LLMProvider, MemoryProvider,
        ConversationRepository, PluginRegistry, ConversationEngine, Agent —
        без состояния конкретного разговора (состояние живёт внутри
        Conversation, который хранит ConversationRepository).
      - Resource: PluginManager — явный init/shutdown жизненного цикла.
      - ExecutionContext НЕ регистрируется здесь — transient-данные
        конкретного вызова инструмента.
    """

    config = providers.Singleton(get_settings)

    # временно; заменится PluginLoader в Итерации 10
    plugins: providers.Provider[list[Plugin]] = providers.Object([])

    openai_api_key = providers.Callable(_unwrap_secret, config.provided.openai_api_key)

    openai_client = providers.Singleton(
        OpenAIClient,
        api_key=openai_api_key,
        timeout=config.provided.openai_timeout,
    )

    llm_provider = providers.Singleton(
        OpenAIProvider,
        client=openai_client,
        model=config.provided.openai_model,
    )

    memory_provider = providers.Singleton(InMemoryMemoryProvider)

    conversation_repository = providers.Singleton(InMemoryConversationRepository)

    plugin_registry = providers.Singleton(SimplePluginRegistry)

    plugin_manager = providers.Resource(
        _init_plugin_manager,
        plugins=plugins,
        registry=plugin_registry,
    )
    tool_manager = providers.Singleton(
        SimpleToolManager,
        tools=[],
    )

    context_builder = providers.Singleton(SimpleContextBuilder)

    conversation_engine = providers.Singleton(
        ToolConversationEngine,
        llm_provider=llm_provider,
        context_builder=context_builder,
        tool_manager=tool_manager,
        memory_provider=memory_provider,
    )

    agent = providers.Singleton(
        SimpleAgent,
        conversation_engine=conversation_engine,
        conversation_repository=conversation_repository,
    )
