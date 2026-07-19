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
* ExecutionContext — реестр capabilities для инструментов (memory, knowledge,
  ingestion), НЕ service locator: технические зависимости (database,
  embedding_provider, settings, logger) сюда не кладём
* Tool Calling Loop
* RememberTool / SearchMemoryTool
* IngestDocumentTool / SearchKnowledgeTool

Принцип tool-слоя: Agent → Tool → Capability → Infrastructure. Инструмент
никогда не оркестрирует инфраструктуру сам (не знает про extractor / chunker /
add_batch / embeddings) — он лишь открывает агенту доступ к уже существующей
capability через ExecutionContext. Tool-слой остаётся тонким.

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

### Knowledge (RAG) — retrieval MVP
* KnowledgeProvider (ABC): add / add_batch / search → list[KnowledgeChunk]
  (не list[str]: source + metadata нужны для цитирования и будущего scoring)
* KnowledgeChunk — доменная модель, ОТДЕЛЬНАЯ от MemoryEntry: память и знания
  разные сущности, их поля со временем расходятся (memory: user-specific,
  created_at; knowledge: source, chunk, document, citations). Дублирование
  честное, переиспользование создало бы ложную связанность
* InMemoryKnowledgeProvider — substring-поиск, доказывает retrieval pipeline
  (Knowledge → Context → LLM) отдельно от хранения; не переживает рестарт
* SqliteKnowledgeProvider — persistent substring-хранилище (KnowledgeRecord),
  переживает рестарт
* SemanticSqliteKnowledgeProvider — semantic-поиск по cosine поверх sqlite;
  save-always (чанк сохраняется даже при сбое embeddings, embedding = NULL) +
  substring-добор для NULL-эмбеддингов; политику отбора применяет ranker
* Knowledge Ranking (зеркало memory): KnowledgeRanker (ABC) +
  ThresholdKnowledgeRanker; провайдер собирает KnowledgeMatch (chunk + score +
  match_type), ranker применяет порог (knowledge_similarity_threshold=0.25) →
  sort → append substring → limit. Наружу — list[KnowledgeChunk], контракт
  KnowledgeProvider.search() неизменен. threshold/min_score НЕ в сигнатуре
  rank() — следующий ранкер (MMR/recency/citation) не меняет интерфейс
* выбор провайдера знаний — providers.Selector по вычисляемому ключу
  (knowledge_backend × knowledge_search_mode), симметрично памяти
* KnowledgeRecord — отдельная таблица (knowledge) с nullable embedding-колонкой
* KnowledgeContextLayer активен: ищет по последнему USER-сообщению (как память,
  чтобы не искать по tool-выводам) и инъектирует чанки system-сообщением
* Chunking Engine: Chunker (ABC, метод split) + FixedSizeChunker — чистый
  алгоритм text → KnowledgeChunk[], без файлов/DI (потребитель — ingestion #19).
  Word-based greedy packing (не режет слова, пробелы нормализуются), инвариант
  len(content) <= chunk_size ВСЕГДА (слово длиннее размера режется жёстко),
  overlap по границам слов. id чанка = sha256(source + content) —
  детерминирован и устойчив к сдвигам содержимого (в отличие от source#index)
* Document Ingestion: DocumentExtractor (ABC, async extract(content: bytes) → str)
  + PlainTextExtractor (utf-8) + DocumentIngestionService (тонкая оркестрация:
  extract → strip → пусто→[] → split → add_batch → return list[KnowledgeChunk]).
  Сервис НЕ знает про формат (весь format-роутинг — внутри extractor) и не несёт
  логики сверх оркестрации (ни логов, ни retries, ни dedup) — новый формат =
  новый DocumentExtractor, пайплайн не меняется. chunker в DI с дефолтами
  (settings chunk_size/overlap появятся с UI/CLI-потребителем). После появления
  внешнего потребителя (Knowledge Tools) контракт сервиса — публичный
* Knowledge Tools: IngestDocumentTool (Tool → DocumentIngestionService) +
  SearchKnowledgeTool (Tool → KnowledgeProvider.search). Замыкают контур
  Agent ↔ Knowledge: агент читает текст → сохраняет → находит → использует.
  Формат ответа search'а блочный (Source + content) — расширяем под будущие
  поля (section/page/relevance) без слома структуры. Knowledge MVP закрыт;
  list_sources/delete_source (расширение контракта провайдера) — отдельный PR
* Структурная симметрия Memory/Knowledge выдержана намеренно (Sqlite* и
  SemanticSqlite* провайдеры, *Ranker + *Match + MatchType в обеих подсистемах),
  даже ценой похожего кода — дерево проекта самодокументирует эволюцию
* Ranker НЕ обобщён в Ranker[T]: потребителей ranking два (memory, knowledge),
  порог genericization — третий независимый потребитель. MemoryMatch.entry vs
  KnowledgeMatch.chunk и продублированный MatchType — честная независимость;
  обобщение отложено до появления устойчивой общей модели
* cosine_similarity вынесена в app/utils/ (чистая математика, не доменный
  контракт → не в core); переиспользуется памятью и знаниями без связывания
  подсистем друг с другом

### Persistence
* app/persistence/ — SQLAlchemy async engine + ORM (MemoryRecord, KnowledgeRecord)
* Domain (app/core/, app/models/) свободен от SQLAlchemy; перевод
  Entry/Chunk ↔ Record живёт в соответствующем провайдере
* Схема поднимается через create_all при инициализации engine-ресурса;
  таблиц теперь две (memories, knowledge) — Alembic станет нужен, когда схема
  начнёт эволюционировать (миграции существующих данных)
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
    ├── KnowledgeContextLayer    (last USER message → KnowledgeProvider.search())
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

### Knowledge (RAG)
* Extractors: Markdown / PDF / DOCX / HTML / RemoteUrl (адаптер за DocumentExtractor)
* Knowledge Management Tools (agent-facing ingest/list/delete)
* Chunking-стратегии: sentence / paragraph / recursive / token / semantic
* Ranking-стратегии: recency / MMR / citation weight / source priority

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
