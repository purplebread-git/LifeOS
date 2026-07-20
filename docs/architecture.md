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
* ListSourcesTool / DeleteSourceTool

Принцип tool-слоя (общий паттерн LifeOS): `Infrastructure → Capability → Tool →
Agent`. Инструмент никогда не оркестрирует инфраструктуру сам (не знает про
extractor / chunker / add_batch / embeddings / SQL) — он лишь открывает агенту
доступ к уже существующей capability через ExecutionContext. Инфраструктурные
детали полностью скрыты, tool-слой остаётся тонким. Наблюдаемая (но пока не
выделенная) точка абстракции — повторяющийся шаблон инструмента: проверить
capability → вызвать → отформатировать результат → вернуть ToolResult; при 4
инструментах абстрагировать преждевременно (правило третьего потребителя).

### Plugins (Phase 2)

Инвариант расширения платформы (после Plugin Contributed Tool):

**Composition Root — единственная точка подключения платформенных расширений.**

Если для подключения нового Plugin требуется менять что-либо кроме composition
root (`container.py`) или самого Plugin, модель расширения нарушена.

Цепочка:

```
Application → Container → PluginManager → PluginRegistry → Plugin → (Tool | ContextLayer | DocumentExtractor)
```

Следствия, уже подтверждённые кодом:

* Agent / ConversationEngine / SimpleToolManager / LayeredContextBuilder /
  ExtractorRegistry / DocumentIngestionService не знают о плагинах;
* вклад (Tool / layer / extractor) не знает, встроенный он или пришёл из плагина;
* `PluginRegistry.all_registered_*()` — только для composition root.

Доказанные оси:

* Plugin → Tool (`EchoPlugin`)
* Plugin → ContextLayer (`CurrentTimePlugin`)
* Plugin → DocumentExtractor (`UppercaseTextPlugin`, `.upper`)

**Plugin API Status:** Proven for Tool, ContextLayer and DocumentExtractor.
Further evolution requires new extension categories or demonstrated limitations
of the current API. (Нет PluginLoader / generic `register(...)` — сознательно,
не упущение; см. `docs/plugin-api-review.md`.)

Аудит API: `docs/plugin-api-review.md`. После трёх осей PluginLoader / generic
registry по-прежнему не вводятся без нового факта.

### Streaming

Инвариант: **Streaming изменяет только способ доставки результата, но не
семантику выполнения агента.**

* `LLMProvider.generate` и `LLMProvider.stream` сосуществуют;
* `ConversationEngine.run_turn` и `stream_turn` — параллельные пути;
* acceptance: склеенный stream == текст `generate()`;
* streaming tool calls / SSE / cancellation — вне текущего MVP.

### Принцип процесса (Phase 1–2)

Помимо «обобщать после трёх потребителей»:

**Новая инфраструктура появляется только после нескольких независимых
подтверждений одной и той же гипотезы.**

Этим объясняется отсутствие BaseExtractor, GenericRanker, GenericMatch,
PluginLoader и универсального `register(...)`: пока нет достаточного числа
независимых подтверждений, платформа не усложняется.

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
  resolve extractor → extract → strip → пусто→[] → split → add_batch → return
  list[KnowledgeChunk]). Сервис не несёт логики сверх оркестрации (ни логов, ни
  retries, ни dedup). chunker в DI с дефолтами (settings chunk_size/overlap
  появятся с UI/CLI-потребителем). После появления внешнего потребителя
  (Knowledge Tools) контракт сервиса — публичный
* Extractor Routing: ExtractorRegistry (extension → DocumentExtractor, default →
  PlainText). Роутинг живёт в реестре, а не в сервисе и не в extractor'е:
  реестр знает source, extractor остаётся узким (bytes → text). Ключ —
  расширение из source, регистронезависимо; неизвестное/без расширения →
  default. Расширение — текущая стратегия сопоставления, а не сущность:
  публичный контракт resolve(source) открыт к MIME / magic bytes /
  resolve(source, content) без слома; ResolutionStrategy как абстракция пока не
  вводится (правило трёх). Архитектурный инвариант: после ввода реестра
  DocumentIngestionService больше НЕ меняется при добавлении форматов —
  новый формат = запись в реестре + новый DocumentExtractor
* MarkdownExtractor: первый нетривиальный extractor (формат .md/.markdown).
  Парсинг делегирован markdown-it-py (CommonMark), а ПОЛИТИКА извлечения текста
  (заголовки/emphasis/ссылки→видимый текст/inline+fenced code/списки/blockquote;
  images и HTML игнорируются) — доменная логика LifeOS: обход токенов внутри
  extractor'а, без промежуточного HTML и без внешнего mdit-plain (чтобы будущие
  изменения политики были локальными). Политика явно зафиксирована в docstring.
  Подключён БЕЗ единой правки DocumentIngestionService/Chunker/KnowledgeProvider/
  Tool/Agent — только регистрацией в реестре: первое сильное подтверждение, что
  ingestion открыт для горизонтального расширения
* PdfExtractor: первый БИНАРНЫЙ формат (.pdf) через тот же контракт bytes → text.
  Парсинг делегирован pypdf (BSD-3, pure Python). Узкая политика: только
  встроенный текстовый слой; без OCR; страница-скан → пустой вклад; документ без
  текста → ""; страницы соединяются \n; ошибки чтения PDF НЕ подавляются
  (собственный ExtractorError не вводится ради одного формата — появится, если
  станет общим для трёх+). Подключён так же — регистрацией .pdf в реестре, без
  изменений остального пайплайна: расширяемость подтверждена уже на двух
  принципиально разных классах документов (текстовый и бинарный)
* Инвариант подсистемы (tests): любой extractor сводит документ к обычному тексту
  — единому «языку» пайплайна (extract → text → chunker → knowledge). Проверяется
  не для формата, а для всей подсистемы (напр. README.md и manual.pdf дают
  одинаковое текстовое представление). После трёх реализаций (PlainText / Markdown
  / Pdf) — точка для анализа реальной (а не ожидаемой) повторяемости перед любым
  BaseExtractor / общими утилитами
* Knowledge Tools: IngestDocumentTool (Tool → DocumentIngestionService) +
  SearchKnowledgeTool (Tool → KnowledgeProvider.search). Замыкают контур
  Agent ↔ Knowledge: агент читает текст → сохраняет → находит → использует.
  Формат ответа search'а блочный (Source + content) — расширяем под будущие
  поля (section/page/relevance) без слома структуры
* Knowledge Source Management: контракт KnowledgeProvider расширен вокруг
  сущности source — list_sources() → list[str] (уникальные, отсортированные) и
  delete_source(source) → int (число удалённых чанков). delete_source
  идемпотентен: несуществующий источник → 0, без исключения. Реализовано во всех
  трёх провайдерах (In-Memory, Sqlite, SemanticSqlite). Агентские инструменты —
  ListSourcesTool / DeleteSourceTool. После этого доменная модель Knowledge
  вокруг source завершена; statistics / rename / delete_chunk сознательно
  отложены. DocumentIngestionService.ingest() и KnowledgeProvider.search()/
  .list_sources()/.delete_source() имеют внешних потребителей → это стабильный
  публичный контракт, изменения сигнатур должны быть осознанными
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

Phase 1 (Core Runtime) завершена. Дальше — фазы поверх платформы
(см. `docs/roadmap.md`). Приоритет: Plugins → Streaming → Observability →
MCP → Multi-Agent → Web UI.

### Phase 2 — Platform
* Plugin lifecycle ✅ — `PluginManager` в Container Resource и FastAPI lifespan.
* Plugin Contributed Tool ✅ — `EchoPlugin` → Tool через `PluginRegistry`.
* Plugin Contributed ContextLayer ✅ — `CurrentTimePlugin` → ContextLayer;
  composition root собирает ContextBuilder из core + plugin layers.
  Agent / ConversationEngine / `LayeredContextBuilder` не менялись.
* Plugin API Review ✅ — `docs/plugin-api-review.md` (вариант А: идти к
  третьей оси без инфраструктурного PR).
* Plugin → DocumentExtractor ✅ — `UppercaseTextPlugin` (`.upper`); три оси;
  Echo/CurrentTime не менялись; ExtractorRegistry/Ingestion без правок под плагин.
* Plugin API frozen until new evidence ✅ — не ищем четвёртую ось искусственно.
* LLM Streaming MVP ✅ — `LLMProvider.stream` + `ConversationEngine.stream_turn`.
  Инвариант: Streaming изменяет только способ доставки результата, но не
  семантику выполнения агента (`''.join(stream) == generate().text`).
  Tool-calls / SSE / cancel — отдельные PR.
* Streaming Tool Calls
* Streaming FastAPI endpoint
* Observability

### Core extensions (не блокируют Phase 2)
* Memory: recency / hybrid / MMR; rebuild_embeddings; query builder
* Context: Token Budget / Trimming / Composer — когда слоёв станет больше
* Knowledge: DOCX / HTML / RemoteUrl; chunking-стратегии; ranking-расширения

### Позже
* Connectivity: MCP / External Services / Integrations
* Intelligence: Multi-Agent / Planning / Long-running Tasks
* UX: Web UI

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
