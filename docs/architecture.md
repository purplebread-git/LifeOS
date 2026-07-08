# LifeOS Agent — Architecture

## Принцип

Agent ничего не знает о конкретных внешних сервисах (Telegram, Notion, GitHub и т.д.).

Он знает только про абстракции:

- LLMProvider
- MemoryProvider
- Tool
- Plugin
- Event

---

## Поток данных

User
→ Conversation Engine
→ Context Builder
→ LLM Provider
→ Tool Manager
→ Plugins
→ External APIs

---

## Правило направления зависимостей

core/
← ничего не импортирует из providers/plugins/memory/api/container.py

↑

models/
← core может импортировать models
← models ничего не знает про core

↑

providers/ plugins/ memory/
← знают про core и models
← не знают друг друга

↑

api/ container.py
← знают про всё
← собирают граф зависимостей

---

## Реализовано

### Core

- Tool
- Plugin
- PluginRegistry
- PluginManager
- ToolManager

### Providers

- OpenAIProvider

### Infrastructure

- Dependency Injector
- FastAPI
- Health endpoint

### Tests

- Ruff
- MyPy
- Pytest

Текущий статус:

- Ruff ✅
- MyPy ✅
- Pytest ✅

Последний результат:

```text
15 passed
```

---

## Важные решения

### ToolManager

Обрабатывает только:

- ToolExecutionError

Не обрабатывает:

- RuntimeError
- ValueError
- Exception

Неожиданные ошибки должны подниматься вверх.

### Models

Использовать:

- app/models/message.py
- app/models/tool.py

Не использовать:

- app/core/models.py

Причина:

core/models.py содержит устаревшие дубликаты моделей.

---

## Следующий этап

Conversation Engine Tool Loop

Нужно реализовать:

1. Получение tool calls от LLM
2. Выполнение через ToolManager
3. Возврат ToolResult в контекст диалога
4. Повторный вызов LLM
5. Завершение цикла при отсутствии tool calls

---

## Как продолжать проект в новом чате

1. Прочитать этот файл.
2. Прочитать docs/roadmap.md.
3. Посмотреть текущий git diff.
4. Продолжить работу с пункта "Следующий этап".