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
from app.knowledge.document_ingestion_service import DocumentIngestionService
from app.knowledge.extractor_registry import ExtractorRegistry
from app.knowledge.fixed_size_chunker import FixedSizeChunker
from app.knowledge.in_memory_knowledge_provider import InMemoryKnowledgeProvider
from app.knowledge.markdown_extractor import MarkdownExtractor
from app.knowledge.pdf_extractor import PdfExtractor
from app.knowledge.plain_text_extractor import PlainTextExtractor
from app.knowledge.semantic_sqlite_knowledge_provider import SemanticSqliteKnowledgeProvider
from app.knowledge.sqlite_knowledge_provider import SqliteKnowledgeProvider
from app.knowledge.threshold_knowledge_ranker import ThresholdKnowledgeRanker
from app.memory.in_memory_provider import InMemoryMemoryProvider
from app.memory.semantic_sqlite_memory_provider import SemanticSqliteMemoryProvider
from app.memory.sqlite_memory_provider import SqliteMemoryProvider
from app.memory.threshold_memory_ranker import ThresholdMemoryRanker
from app.persistence.database import init_database
from app.plugins.manager import SimplePluginManager
from app.plugins.registry import SimplePluginRegistry
from app.providers.openai import OpenAIClient, OpenAIEmbeddingProvider, OpenAIProvider
from app.tools import (
    DeleteSourceTool,
    IngestDocumentTool,
    ListSourcesTool,
    RememberTool,
    SearchKnowledgeTool,
    SearchMemoryTool,
)
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


def _knowledge_provider_key(settings: Settings) -> str:
    """Выбор провайдера знаний по (backend × search_mode). Симметрично памяти:
    semantic — режим поиска поверх sqlite, а не отдельный backend. memory +
    semantic пока падает в substring (in-memory semantic вне текущего scope)."""
    if settings.knowledge_backend == "memory":
        return "memory"
    if settings.knowledge_search_mode == "semantic":
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

    # Список плагинов задаётся composition root'ом. Discovery / entry points /
    # hot reload — следующие PR; сейчас достаточно явного списка (пока пустого).
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

    # Knowledge (RAG): провайдер знаний выбирается по (backend × search_mode),
    # симметрично памяти. semantic — режим поиска поверх sqlite. Ranking —
    # отдельная инъектируемая стратегия (зеркало memory_ranker), память не
    # затрагивает: подсистемы эволюционируют независимо.
    in_memory_knowledge_provider = providers.Singleton(InMemoryKnowledgeProvider)

    sqlite_knowledge_provider = providers.Singleton(
        SqliteKnowledgeProvider,
        session_factory=database,
    )

    knowledge_ranker = providers.Singleton(
        ThresholdKnowledgeRanker,
        min_score=config.provided.knowledge_similarity_threshold,
    )

    semantic_sqlite_knowledge_provider = providers.Singleton(
        SemanticSqliteKnowledgeProvider,
        session_factory=database,
        embedding_provider=embedding_provider,
        ranker=knowledge_ranker,
    )

    knowledge_provider = providers.Selector(
        providers.Callable(_knowledge_provider_key, config),
        memory=in_memory_knowledge_provider,
        sqlite=sqlite_knowledge_provider,
        semantic_sqlite=semantic_sqlite_knowledge_provider,
    )

    # Ingestion pipeline: extractor (bytes→text) → chunker (text→chunks) →
    # knowledge_provider.add_batch. Chunker с дефолтами (settings появятся, когда
    # будет UI/CLI-потребитель тюнинга). Формат-роутинг живёт в ExtractorRegistry
    # (по расширению source, default → PlainText); новый формат = запись в реестре
    # + новый DocumentExtractor, без изменений DocumentIngestionService.
    markdown_extractor = providers.Singleton(MarkdownExtractor)

    extractor_registry = providers.Singleton(
        ExtractorRegistry,
        default=providers.Singleton(PlainTextExtractor),
        extractors=providers.Dict(
            {
                ".md": markdown_extractor,
                ".markdown": markdown_extractor,
                ".pdf": providers.Singleton(PdfExtractor),
            }
        ),
    )

    chunker = providers.Singleton(FixedSizeChunker)

    document_ingestion_service = providers.Singleton(
        DocumentIngestionService,
        extractor_registry=extractor_registry,
        chunker=chunker,
        knowledge_provider=knowledge_provider,
    )

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
            IngestDocumentTool(),
            SearchKnowledgeTool(),
            ListSourcesTool(),
            DeleteSourceTool(),
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
        knowledge_provider=knowledge_provider,
        ingestion_service=document_ingestion_service,
    )

    agent = providers.Singleton(
        SimpleAgent,
        conversation_engine=conversation_engine,
        conversation_repository=conversation_repository,
    )
