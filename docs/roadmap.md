Roadmap

Phase 1 — Foundation

Базовый каркас агентной системы.

Done

* Domain Models
* Message
* Conversation
* AgentResponse
* Core Interfaces
* Agent
* LLMProvider
* ConversationRepository
* OpenAIProvider
* OpenAI Response Mapping
* Typed Models
* Error Handling
* InMemoryConversationRepository
* Dependency Injection Container
* SimpleAgent
* Real LLM Integration

⸻

Phase 2 — Tooling & ReAct

Добавление инструментов и циклов выполнения.

Done

* Tool Interface
* ToolManager
* Tool Registry
* ExecutionContext
* Tool Calling Models
* Tool Call Parsing
* Tool Result Processing
* ToolConversationEngine
* ReAct Loop

Remaining

* Tool Validation Layer
* Tool Permissions
* Tool Categories

⸻

Phase 3 — Memory

Создание долговременной памяти агента.

Done

* MemoryEntry
* MemoryProvider Interface
* InMemoryMemoryProvider
* RememberTool
* SearchMemoryTool
* Memory Integration Through Tools

Current Iteration

* Memory Context Integration

Planned Scope

* Search relevant memories before LLM call
* Inject memories into prompt context
* Top-K memory selection
* Memory formatting strategy
* Unit tests
* Integration tests

Future Memory Work

* Persistent MemoryProvider
* SQLite Memory Provider
* Vector Memory Provider
* Semantic Search
* Relevance Ranking
* Memory Expiration Policies
* Memory Summarization

⸻

Phase 4 — Context System

Формирование интеллектуального контекста.

Planned

* ContextBuilder
* Context Layers
* System Context
* Memory Context
* Conversation Context
* Context Trimming
* Token Budget Management

⸻

Phase 5 — Knowledge

Работа со знаниями и документами.

Planned

* Knowledge Base
* Document Storage
* RAG Pipeline
* Embeddings
* Search Layer

⸻

Phase 6 — Platform

Развитие платформы.

Planned

* Plugin System
* MCP Integration
* Streaming
* Observability
* Metrics
* Tracing
* Configuration System

⸻

Phase 7 — Agent Ecosystem

Переход к сложным агентным сценариям.

Planned

* Multi-Agent Architecture
* Agent Registry
* Agent Collaboration
* Task Delegation

⸻

Interfaces Status

Stable

* Agent
* LLMProvider
* ConversationRepository
* MemoryProvider
* Tool

Under Active Development

* ContextBuilder

Not Started

* KnowledgeProvider
* PluginProvider

⸻

Current Focus

Memory Context Integration

Цель:

Агент должен автоматически использовать релевантные воспоминания при построении контекста без необходимости явного вызова memory-инструментов.