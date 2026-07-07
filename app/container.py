"""Composition root приложения.

app/core/ НИКОГДА не импортирует dependency-injector — библиотека
используется исключительно здесь, на границе wiring'а.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from dependency_injector import containers, providers

from app.config.settings import get_settings
from app.core.plugin import Plugin
from app.memory.in_memory_provider import InMemoryMemoryProvider
from app.plugins.manager import SimplePluginManager
from app.plugins.registry import SimplePluginRegistry
from app.providers.null_llm_provider import NullLLMProvider
from app.stubs import StubAgent, StubContextBuilder, StubConversationEngine


async def _init_plugin_manager(
    plugins: list[Plugin],
    registry: SimplePluginRegistry,
) -> AsyncIterator[SimplePluginManager]:
    """Resource-провайдер жизненного цикла плагинов.

    Запускает плагины при старте и останавливает их в обратном порядке
    при shutdown_resources().
    """
    manager = SimplePluginManager(
        plugins=plugins,
        registry=registry,
    )

    await manager.start()

    try:
        yield manager
    finally:
        await manager.stop()


class Container(containers.DeclarativeContainer):
    """Граф зависимостей приложения.

    Lifetimes:

    Singleton:
      - сервисы приложения с общим состоянием процесса:
        LLMProvider, MemoryProvider, PluginRegistry,
        ConversationEngine, Agent.

    Resource:
      - компоненты с явным lifecycle:
        PluginManager.

    Transient:
      - Conversation и ExecutionContext создаются
        на уровне конкретного запроса.
    """

    config = providers.Singleton(get_settings)

    # Временно пустой источник плагинов.
    # В Итерации 8 заменится на PluginLoader.
    plugins = providers.Callable(lambda: [])

    llm_provider = providers.Singleton(
        NullLLMProvider,
    )

    memory_provider = providers.Singleton(
        InMemoryMemoryProvider,
    )

    plugin_registry = providers.Singleton(
        SimplePluginRegistry,
    )

    plugin_manager = providers.Resource(
        _init_plugin_manager,
        plugins=plugins,
        registry=plugin_registry,
    )

    context_builder = providers.Singleton(
        StubContextBuilder,
    )

    conversation_engine = providers.Singleton(
        StubConversationEngine,
        llm_provider=llm_provider,
        context_builder=context_builder,
    )

    agent = providers.Singleton(
        StubAgent,
        conversation_engine=conversation_engine,
        memory_provider=memory_provider,
    )