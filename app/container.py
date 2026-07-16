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
    ToolConversationEngine,
)
from app.config.settings import Settings, get_settings
from app.context import (
    DEFAULT_SYSTEM_PROMPT,
    ConversationHistoryLayer,
    KnowledgeContextLayer,
    LayeredContextBuilder,
    MemoryContextLayer,
    SystemPromptLayer,
)
from app.conversation.in_memory_repository import InMemoryConversationRepository
from app.core.plugin import Plugin
from app.knowledge.in_memory_knowledge_provider import InMemoryKnowledgeProvider
from app.memory.in_memory_provider import InMemoryMemoryProvider
from app.memory.semantic_sqlite_memory_provider import SemanticSqliteMemoryProvider
from app.memory.sqlite_memory_provider import SqliteMemoryProvider
from app.memory.threshold_memory_ranker import ThresholdMemoryRanker
from app.persistence.database import init_database
from app.plugins.manager import SimplePluginManager
from app.plugins.registry import SimplePluginRegistry
from app.providers.openai import OpenAIClient, OpenAIEmbeddingProvider, OpenAIProvider
from app.tools import RememberTool, SearchMemoryTool
from app.tools.simple_tool_manager import SimpleToolManager


def _unwrap_secret(secret: SecretStr) -> str:
    return secret.get_secret_value()


def _memory_provider_key(settings: Settings) -> str:
    """Выбор провайдера памяти по (backend × search_mode).

    semantic — режим поиска поверх sqlite, а не отдельный backend. Поэтому
    ключ вычисляется, а Selector остаётся одномерным. memory + semantic пока
    падает в substring (in-memory semantic вне текущего scope)."""
    if settings.memory_backend == "memory":
        return "memory"
    if settings.memory_search_mode == "semantic":
        return "semantic_sqlite"
    return "sqlite"


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
      - Resource: PluginManager, database (engine) — явный init/shutdown
        жизненного цикла.
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

    embedding_provider = providers.Singleton(
        OpenAIEmbeddingProvider,
        client=openai_client,
        model=config.provided.openai_embedding_model,
    )

    database = providers.Resource(
        init_database,
        database_url=config.provided.database_url,
    )

    in_memory_provider = providers.Singleton(InMemoryMemoryProvider)

    sqlite_memory_provider = providers.Singleton(
        SqliteMemoryProvider,
        session_factory=database,
    )

    # Retrieval pipeline: провайдер собирает кандидатов, ranker применяет
    # политику (порог/сортировка/лимит). Смена стратегии ранжирования —
    # замена одного provider, storage не трогаем.
    memory_ranker = providers.Singleton(
        ThresholdMemoryRanker,
        min_score=config.provided.memory_similarity_threshold,
    )

    semantic_sqlite_memory_provider = providers.Singleton(
        SemanticSqliteMemoryProvider,
        session_factory=database,
        embedding_provider=embedding_provider,
        ranker=memory_ranker,
    )

    # Provider Pattern: провайдер памяти выбирается по (backend × search_mode).
    # semantic — режим поиска поверх sqlite, а не отдельный backend.
    memory_provider = providers.Selector(
        providers.Callable(_memory_provider_key, config),
        memory=in_memory_provider,
        sqlite=sqlite_memory_provider,
        semantic_sqlite=semantic_sqlite_memory_provider,
    )

    # Knowledge (RAG-задел): in-memory substring-провайдер. Доказывает
    # retrieval pipeline (Knowledge → Context → LLM) отдельно от хранения;
    # persistence/semantic — отдельные шаги, как это было с памятью.
    knowledge_provider = providers.Singleton(InMemoryKnowledgeProvider)

    conversation_repository = providers.Singleton(InMemoryConversationRepository)

    plugin_registry = providers.Singleton(SimplePluginRegistry)

    plugin_manager = providers.Resource(
        _init_plugin_manager,
        plugins=plugins,
        registry=plugin_registry,
    )
    tool_manager = providers.Singleton(
        SimpleToolManager,
        tools=[
            RememberTool(),
            SearchMemoryTool(),
        ],
    )

    # Context System: порядок слоёв задаётся здесь. Добавление нового слоя
    # (например, Knowledge/RAG) не меняет LayeredContextBuilder.
    context_builder = providers.Singleton(
        LayeredContextBuilder,
        layers=providers.List(
            providers.Singleton(SystemPromptLayer, system_prompt=DEFAULT_SYSTEM_PROMPT),
            providers.Singleton(MemoryContextLayer, memory_provider=memory_provider),
            providers.Singleton(KnowledgeContextLayer, knowledge_provider=knowledge_provider),
            providers.Singleton(ConversationHistoryLayer),
        ),
    )

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
