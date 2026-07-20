# Roadmap

Phase 1 (Core Runtime) завершена. Ядро больше не «строится» — оно стало
платформой. Дальнейшие пункты — возможности поверх стабильного фундамента,
а не архитектурные рефакторинги «на всякий случай».

Общий паттерн ядра: `Infrastructure → Capability → Tool → Agent`.
Принципы абстракций: `docs/architecture-review.md`
(вариативность **или** DIP; обобщать после трёх реальных потребителей).

Приоритет Phase 2+: Plugins → Streaming → Observability → MCP →
Multi-Agent → Web UI.

## Phase 1 — Core Runtime ✅

Цельное ядро: Foundation → Conversation/Tools → Context → Memory →
Knowledge → Document Ingestion → Architecture Review.

### Foundation
- [x] Core interfaces (ABC)
- [x] Domain models
- [x] Dependency Injection Container
- [x] OpenAIProvider
- [x] ConversationRepository
- [x] Real Agent

### Conversation & Tool Calling
- [x] Tool Interface / ToolManager
- [x] ExecutionContext (реестр capabilities)
- [x] ReAct Loop / ToolConversationEngine
- [x] Tool Call Correlation (`tool_call_id` штампует менеджер, не инструмент)

### Context System
- [x] ContextLayer (pipeline contract)
- [x] Layered ContextBuilder (System / Memory / Knowledge / Conversation)
- [ ] Context Composer (когда слоёв станет больше — Phase 2+ по необходимости)
- [ ] Token Budget / Context Trimming

### Memory
Storage → Retrieval → Ranking → Context → LLM.
- [x] Memory Storage / Context Integration / Persistent / Semantic / Ranking

### Knowledge
Зеркальная схема памяти; доменная модель вокруг `source`.
- [x] KnowledgeProvider + KnowledgeChunk + Context Layer
- [x] Persistent / Semantic / Ranking
- [x] Chunking + Document Ingestion + Source Management
- [x] Extractor Routing (ExtractorRegistry)
- [x] PlainText / Markdown / PDF Extractors

### Capabilities (agent-facing)
- [x] Memory Tools / Knowledge Tools / Source Tools

### Architecture Review
- [x] `docs/architecture-review.md` — принципы и статус абстракций

### Core extensions (опционально, не блокируют Phase 2)
- [ ] Extractor analysis / DOCX / HTML / RemoteUrl
- [ ] Memory: Recency / Hybrid / MMR / Maintenance
- [ ] Knowledge: chunking-стратегии, ranking-расширения, statistics/rename

## Phase 2 — Platform

Модель расширения поверх стабильного ядра. Скелет уже есть
(`Plugin` / `PluginRegistry` / `PluginManager` / `SimplePluginManager`) —
нужны реальные интеграции и wiring, а не новые абстракции «впрок».

- [ ] Plugins (первый приоритет Phase 2)
- [ ] Streaming
- [ ] Observability

## Phase 3 — Connectivity

- [ ] MCP
- [ ] External Services
- [ ] Integrations

## Phase 4 — Intelligence

- [ ] Multi-Agent / Agent Registry / Task Delegation
- [ ] Planning
- [ ] Long-running Tasks

## Phase 5 — User Experience

- [ ] Web UI

## Next

**Plugins** — точка входа в Phase 2. Streaming и Observability строятся уже
поверх стабильной модели расширения, а не наоборот.
