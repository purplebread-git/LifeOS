LifeOS Agent — Architecture Status

## Completed

### Foundation
* Core interfaces (ABC)
* DI Container (dependency-injector)
* OpenAIProvider (+ нормализация: mapper, TypedDict, SecretStr, exceptions)
* ConversationRepository + InMemoryConversationRepository
* Real Agent (SimpleAgent)

### Tooling & ReAct
* ToolManager
* ReAct ConversationEngine (ToolConversationEngine)
* ExecutionContext
* Tool Calling Loop
* RememberTool
* SearchMemoryTool

### Memory
* MemoryProvider (ABC)
* InMemoryMemoryProvider
* SqliteMemoryProvider (async SQLAlchemy, память переживает рестарт)
* SemanticSqliteMemoryProvider (embeddings + cosine поверх sqlite)
* EmbeddingProvider (ABC) + OpenAIEmbeddingProvider
* Memory Tool Integration (remember / search_memory via ExecutionContext)
* Memory Context Integration (автоматическая инъекция памяти в LLM-контекст)

Semantic search:
* MemoryProvider.search() контракт НЕ менялся — провайдер сам эмбеддит запрос
* save-always: запись сохраняется даже при сбое embeddings (embedding = NULL)
* search: нет эмбеддинга запроса → substring по всем; иначе semantic по
  записям с эмбеддингом + substring-добор для записей с embedding IS NULL
* похожесть — brute-force cosine (pgvector / sqlite-vec — будущее)

Memory Ranking (retrieval pipeline):
* MemoryRanker (ABC) + ThresholdMemoryRanker — политика отбора вынесена из
  провайдера в инъектируемую стратегию
* провайдер собирает MemoryMatch (entry + score + match_type: semantic |
  substring); ranker применяет порог → sort → limit и возвращает list[MemoryEntry]
* semantic-кандидаты проходят при score >= memory_similarity_threshold (0.25
  по умолчанию, Field ge=0.0/le=1.0); substring-кандидаты (точное совпадение
  на записи без эмбеддинга) порог обходят — политика целиком внутри ranker
* limit применяется ПОСЛЕ порога и сортировки
* смена стратегии (recency / dedup / hybrid / MMR) = новый MemoryRanker в
  контейнере, storage не трогаем

### Context System
* ContextLayer (ABC, pipeline-контракт apply)
* LayeredContextBuilder — app/context/
* Слои: SystemPromptLayer, MemoryContextLayer, KnowledgeContextLayer (stub),
  ConversationHistoryLayer
* SimpleContextBuilder — reference-реализация (conversation-only)

### Knowledge (контракт-задел)
* KnowledgeProvider (ABC) — без реализации, DI и использования; зафиксирован
  контракт, чтобы KnowledgeContextLayer не рефакторить при подключении RAG

### Persistence
* app/persistence/ — SQLAlchemy async engine + ORM (MemoryRecord)
* Domain (app/core/, app/models/) свободен от SQLAlchemy; перевод
  MemoryEntry ↔ MemoryRecord живёт в провайдере
* Схема поднимается через create_all при инициализации engine-ресурса;
  Alembic — отдельный PR, когда появится вторая таблица
* Выбор провайдера памяти — providers.Selector по вычисляемому ключу
  (memory_backend × memory_search_mode). semantic — режим поиска поверх
  sqlite, а не отдельный backend

⸻

## Текущий поток: Context Pipeline

```
User Message
    ↓
SimpleAgent.respond()
    ↓
ToolConversationEngine.run_turn()
    ↓
LayeredContextBuilder.build()   — pipeline из ContextLayer.apply()
    ├── SystemPromptLayer        (персона/инструкции)
    ├── MemoryContextLayer       (last USER message → MemoryProvider.search())
    ├── KnowledgeContextLayer    (stub: passthrough, задел под RAG)
    └── ConversationHistoryLayer (копия истории)
    ↓
LLMProvider.generate()
```

Каждый слой — ContextLayer с pipeline-контрактом
`apply(conversation, context) -> context`. Producer-слои добавляют свои
сообщения; будущие transformer-слои (Token Budget, Trimming) смогут
переписать накопленный контекст без слома интерфейса. Порядок и состав
слоёв задаются в Container.

Два независимых пути к памяти:

| Режим | Путь |
|-------|------|
| Автоматический | MemoryContextLayer → MemoryProvider.search() → system prompt |
| Явный (tools) | LLM → remember / search_memory → ExecutionContext.memory |

⸻

## Следующие направления

### Memory
* Ranking-стратегии: recency / dedup / hybrid weighting / MMR (новый MemoryRanker)
* rebuild_embeddings() — reindex при смене embedding-модели или после сбоя
* Memory Search Query Builder — извлечение search query из мультимодальных сообщений (TextBlock + будущие ImageBlock и др.)

### Context System
* Token Budget
* Context Trimming

### Knowledge
* Knowledge Base
* RAG
* Embeddings
* Search Layer

### Platform
* Plugins (реальные интеграции)
* Streaming
* Observability
* MCP
* Multi-agent
* Web UI

⸻

## Известные архитектурные натяжения

### AgentResponse vs Conversation

AgentResponse.messages содержит только новый ответ ассистента, тогда как Conversation.messages хранит полную историю.

Требуется единое решение на этапе развития API.

### Mutable Conversation

ConversationRepository.load() возвращает mutable-объект.

При многопоточном доступе потребуется либо immutable-модель, либо механизм блокировок.

### Memory search — режимы

InMemoryMemoryProvider и SqliteMemoryProvider ищут по substring (LIKE).
SemanticSqliteMemoryProvider (memory_search_mode=semantic) ищет по cosine —
запрос вида «расскажи про меня» находит релевантное. Ranking введён:
ThresholdMemoryRanker отсекает semantic-кандидатов ниже
memory_similarity_threshold (0.25 по умолчанию), поэтому нерелевантный шум
(«столица Франции» → «любит рок») больше не инъектируется.

Semantic — brute-force cosine по всем записям (O(n)). Для персонального
масштаба достаточно; pgvector / sqlite-vec — при росте объёма.

InMemoryMemoryProvider остаётся для разработки и тестов (memory_backend=memory).

### Memory Context — порог отсекает шум

При substring MemoryContextLayer не добавляет system-сообщение, если
совпадений нет. При semantic порог ranker'а отсекает слабые совпадения:
если ничего не проходит threshold, память не инъектируется. Substring-добор
(записи без эмбеддинга) порог обходит — точное совпадение считается сигналом.

### Memory Context Cache (задел, не активен)

SimpleContextBuilder читает `conversation.metadata["memory_context"]` как turn-scoped кэш.
Сейчас никто не записывает это значение — кэш read-only, бага нет.

При активации кэша: ownership должен остаться turn-scoped.
`metadata` сохраняется в репозиторий вместе с Conversation — без очистки
кэш переживёт save/load и вернёт устаревшие воспоминания на следующем turn.

Рекомендация: при включении кэша перенести ownership в ConversationEngine
и очищать ключ до/после `repository.save()`.

### ContextBuilder и Conversation.metadata

ContextBuilder сейчас читает служебное состояние из `Conversation.metadata`.
По мере роста Context System (knowledge_context, token_budget и др.)
это может превратиться в скрытую зависимость. Рассмотреть выделение
turn-scoped execution state в отдельную абстракцию.
