# Roadmap

Инфраструктурный фундамент первой версии завершён (ядро + платформа +
Streaming + SSE). Критерий успеха дальше — не «архитектура стала чище», а
«стало удобнее решать реальные задачи».

Общий паттерн ядра: `Infrastructure → Capability → Tool → Agent`.
Принципы: `docs/architecture-review.md`, `docs/plugin-api-review.md`.

**Приоритет сейчас:** Dogfooding → Observability (по боли) → MCP → Multi-Agent.
Не наоборот.

## Phase 1 — Core Runtime ✅

Foundation → Conversation/Tools → Context → Memory → Knowledge → Ingestion →
Architecture Review. См. историю PR #1–#26.

## Phase 2 — Platform ✅ (фундамент)

Расширяемость и пользовательский API первой версии:

- [x] Plugin lifecycle + Tool / ContextLayer / DocumentExtractor axes
- [x] Plugin API Review + frozen until new evidence
- [x] LLM Streaming MVP + Streaming Tool Calling (один ReAct, два транспорта)
- [x] FastAPI SSE (`POST /v1/chat/stream`)

## Phase 2.5 — Product / Dogfooding ← сейчас

Сквозной путь Client → Agent → Engine → Tools → Memory/Knowledge → LLM готов.
Дальше — жить внутри системы и чинить то, что мешает каждый день.

- [x] Minimal CLI (`lifeos chat`) — точка входа для ежедневного использования
- [ ] Dogfooding fixes (UX, ошибки, команды, память, документы, диалоги) —
      только из реального опыта, не из гипотез
- [ ] Stream cancellation — если болит при использовании
- [ ] Observability — если сложно понимать решения агента

## Phase 3 — Connectivity (после dogfooding)

Приоритеты пересматриваются по итогам использования.

- [ ] MCP
- [ ] External Services / Integrations

## Phase 4 — Intelligence (после dogfooding)

- [ ] Multi-Agent / Planning / Long-running Tasks

## Phase 5 — User Experience

- [ ] Web UI (если CLI перестанет хватать)

## Core extensions (опционально)

- [ ] Context Composer / Token Budget
- [ ] Extra extractors / ranking strategies / memory maintenance

## Next

**Пользоваться LifeOS каждый день** (`uv run lifeos chat`).  
Правила эпохи и критерий успеха: `docs/dogfooding.md`.

Следующие PR — только из реального опыта (что мешало / зачем открывали
ChatGPT). Observability / MCP / Multi-Agent — после 2–4 недель использования
и реальных болей, не по заранее придуманному порядку.
