# LifeOS Agent — Architecture

## Принцип
Agent ничего не знает о конкретных внешних сервисах (Telegram, Notion, GitHub и т.д.).
Он знает только про абстракции:

- LLMProvider
- MemoryProvider
- Tool
- Plugin
- Event

## Поток данных
User → Conversation Engine → Context Builder → LLM Provider → Tool Manager → Plugins → External APIs

## Статус
- [x] Итерация 1: Фундамент (config, app factory, healthcheck)
- [ ] Итерация 2: Базовые интерфейсы (core/interfaces.py)
- [ ] Итерация 3: LLM Provider (OpenAIProvider)
- [ ] Итерация 4: Tool Manager
- [ ] Итерация 5: Agent + Conversation Engine
- [ ] Итерация 6: Memory Provider
- [ ] Итерация 7: Plugins
- [ ] Итерация 8: Интеграции (Telegram, Notion, ...)