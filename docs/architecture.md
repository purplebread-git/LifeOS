LifeOS Agent — Roadmap

* Foundation
* Core interfaces (ABC)
* DI Container (dependency-injector)
* OpenAIProvider (+ нормализация: mapper, TypedDict, SecretStr, exceptions)
* ConversationRepository + InMemoryConversationRepository
* Real Agent (SimpleAgent, stubs.py удалён)

Tooling & ReAct

* ToolManager
* ReAct ConversationEngine (ToolConversationEngine)
* ExecutionContext
* Tool Calling Loop
* RememberTool
* SearchMemoryTool

Memory

* MemoryProvider (ABC)
* InMemoryMemoryProvider
* Memory Tool Integration
* Memory Context Integration
* ContextBuilder
* Production MemoryProvider
* Semantic Search
* Memory Ranking / Relevance

Platform

* Plugins (реальные интеграции)
* Streaming
* Observability
* MCP
* Multi-agent
* Web UI

⸻

Текущая итерация: Memory Context Integration

Цель:

Автоматически использовать релевантную память при построении контекста для LLM без явного вызова инструментов.

Нужно реализовать:

1. Поиск релевантной памяти по последнему сообщению пользователя.
2. Интеграцию найденной памяти в контекст диалога.
3. Ограничение количества воспоминаний (top_k).
4. Форматирование памяти для prompt.
5. Unit-тесты для Memory Context Integration.

⸻

Известные архитектурные натяжения

AgentResponse vs Conversation

AgentResponse.messages содержит только новый ответ ассистента, тогда как Conversation.messages хранит полную историю.

Требуется единое решение на этапе развития API.

Mutable Conversation

ConversationRepository.get_by_id() возвращает mutable-объект.

При многопоточном доступе потребуется либо immutable-модель, либо механизм блокировок.

InMemory Memory Provider

Текущая реализация подходит только для разработки и тестов.

Для production потребуется постоянное хранилище и механизм поиска по памяти.