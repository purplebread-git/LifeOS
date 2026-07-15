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
* Memory Tool Integration (remember / search_memory via ExecutionContext)
* Memory Context Integration (автоматическая инъекция памяти в LLM-контекст)

⸻

## Текущий поток: Memory Context

```
User Message
    ↓
SimpleAgent.respond()
    ↓
ToolConversationEngine.run_turn()
    ↓
SimpleContextBuilder.build()
    ├── last USER message → MemoryProvider.search()
    └── [system: memories] + conversation.messages
    ↓
LLMProvider.generate()
```

Два независимых пути к памяти:

| Режим | Путь |
|-------|------|
| Автоматический | ContextBuilder → MemoryProvider.search() → system prompt |
| Явный (tools) | LLM → remember / search_memory → ExecutionContext.memory |

⸻

## Следующие направления

### Memory
* Semantic Search
* Memory Ranking / Relevance
* Memory Search Query Builder — извлечение search query из мультимодальных сообщений (TextBlock + будущие ImageBlock и др.)
* Persistent MemoryProvider

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

### InMemory Memory Provider

Текущая реализация подходит только для разработки и тестов.

Для production потребуется постоянное хранилище и механизм поиска по памяти.

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
