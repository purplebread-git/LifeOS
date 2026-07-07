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

## Правило направления зависимостей

core/  ← ничего не импортирует из providers/plugins/memory/api/container.py
  ↑
models/  ← core может импортировать models; models ничего не знает про core
  ↑
providers/ plugins/ memory/  ← знают про core и models, не знают друг друга
  ↑
api/ container.py  ← знают про всё, собирают граф зависимостей

## Статус
- [x] Итерация 1: Фундамент
- [x] Итерация 2: Интерфейсы ядра
- [x] Итерация 3: DI Container (dependency-injector)
- [ ] Итерация 4: OpenAIProvider
- [ ] Итерация 5: ToolManager
- [ ] Итерация 6: Agent (реальная реализация, удаление stubs.py)
- [ ] Итерация 7: MemoryProvider (production-реализация)
- [ ] Итерация 8: Plugins