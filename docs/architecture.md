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
* Memory Tool Integration (remember / search_memory via ExecutionContext)
* Memory Context Integration (автоматическая инъекция памяти в LLM-контекст)

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
* Выбор бэкенда памяти — providers.Selector по настройке memory_backend
  (memory | sqlite)

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
* Semantic Search
* Memory Ranking / Relevance
* Memory Search Query Builder — извлечение search query из мультимодальных сообщений (TextBlock + будущие ImageBlock и др.)

### Context System
* Layered ContextBuilder: System / Memory / Conversation / Knowledge
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

### Memory search — substring

И InMemoryMemoryProvider, и SqliteMemoryProvider ищут по substring
(LIKE) без ранжирования и семантики. Запрос вида «расскажи про меня»
ничего не найдёт. Semantic Search / Ranking — отдельные итерации;
интерфейс MemoryProvider.search() при этом не меняется.

InMemoryMemoryProvider остаётся для разработки и тестов (memory_backend=memory).

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
