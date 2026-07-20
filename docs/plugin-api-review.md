# Plugin API Review (Architecture Review II)

Короткий аудит **plugin-системы** после двух независимых осей расширения
(PR #27–#30). Не ревью ядра Phase 1 — оценка того, достаточно ли текущего
Plugin API для третьей оси, или нужна инфраструктурная перестройка.

Основан на фактическом коде, не на планах.

## Что уже доказано

Две независимые оси через один механизм:

```
Composition Root
      │
PluginManager.start()
      │
Plugin.register(registry)
      │
PluginRegistry  ──► tools / context_layers
      │
composition root собирает ToolManager / ContextBuilder
```

| Ось | Плагин | Ядро затронуто? |
|---|---|---|
| Plugin → Tool | `EchoPlugin` | только `container.py` + registry API |
| Plugin → ContextLayer | `CurrentTimePlugin` | только `container.py` + registry API |

`SimpleToolManager` и `LayeredContextBuilder` **не** менялись под плагины.
Инвариант composition root подтверждён повторно.

## Ответы на контрольные вопросы

### 1. Дублирование `register_*` / `all_registered_*`?

Да, пары симметричны (append + snapshot list). Это **честное** дублирование
typed write-side API, а не скрытая бизнес-логика.

С двумя осями обобщать рано (правило трёх). Generic
`register(kind) / all(kind)` или `Registerable[T]` сейчас ухудшил бы ясность:
composition root явно знает, *куда* вставлять tools vs layers (разный порядок
в графе). Typed методы это сохраняют.

**Решение:** оставить как есть. При появлении *третьей* оси — снова
посмотреть, не появилась ли устойчивая общая модель. Не раньше.

### 2. Не становится ли `PluginRegistry` god-object?

Нет. Сейчас это typed bag:

* два списка;
* никакой оркестрации, DI, политики порядка, lifecycle;
* lifecycle остаётся в `PluginManager`;
* порядок слоёв/tools — в composition root.

Registry **знает** типы `Tool` и `ContextLayer` — это осознанная связь с
контрактами платформы, не с Agent/Engine. God-object появился бы, если бы
registry сам собирал ToolManager, решал порядок слоёв или вызывал LLM.

**Решение:** не дробить и не обобщать. Наблюдать при 3+ категориях.

### 3. Все ли точки расширения идут через composition root?

Для **plugin-осей** — да. `all_registered_*` читаются только в
`app/container.py` (`_build_tool_manager`, `_build_context_builder`).
Agent / ConversationEngine / builders registry не импортируют.

Вне plugin-модели остаются «ядровые» wiring'и (например `ExtractorRegistry`
с Markdown/Pdf) — это не нарушение инварианта: плагины туда ещё не ходят.
Третья ось DocumentExtractor как раз должна пройти тот же путь:
plugin → registry → composition root → существующий `ExtractorRegistry` /
ingestion, **без** правок Agent/Engine.

### 4. Не знает ли Plugin слишком много о платформе?

Плагин видит только `PluginRegistry` в `register()` и опционально
startup/shutdown. Он **не** видит Container, Agent, Engine, ToolManager,
ContextBuilder.

Он *создаёт* объекты контрактов, которые вносит (`Tool`, `ContextLayer`) —
это нормально: вклад должен соответствовать публичному контракту capability.
`EchoPlugin` / `CurrentTimePlugin` не импортируют agent/container.

Watch-item: у обоих плагинов `on_startup` / `on_shutdown` — пустые no-op.
Lifecycle API оправдан менеджером (DIP + будущие ресурсы), но пока не
подтверждён реальным потребителем. Не удалять; не усложнять.

### 5. Можно ли добавить третью категорию без изменения существующих плагинов?

**Да.** Новый `register_document_extractor` (или аналог) потребует:

* методов на `PluginRegistry` / `SimplePluginRegistry`;
* wiring в composition root;
* нового Plugin.

`EchoPlugin` и `CurrentTimePlugin` трогать не нужно: они вызывают только
свои `register_*`. ABC плагина (`register` / startup / shutdown) не меняется.

Это сильный сигнал: API расширяется **аддитивно** по осям.

## Вердикт

**Вариант А — API достаточно хорош для третьей оси.**

Не делать сейчас:

* PluginLoader / auto-discovery / entry points;
* generic registry / категории плагинов;
* разбиение PluginRegistry;
* обязательный смысловой startup у каждого плагина.

Следующий продуктовый шаг после этого документа — третья независимая ось
(естественный кандидат: Plugin → DocumentExtractor), тем же инвариантом:
только composition root + registry + новый plugin.

Инфраструктурный PR до третьей оси **не** нужен: необходимости не доказано.
Если при третьей оси появится устойчивое повторение (три одинаковых
register-пары *и* одинаковый wiring-паттерн) — тогда точечный рефакторинг
с фактами, а не впрок.

## Postscript (после Plugin → DocumentExtractor)

Третья ось добавлена аддитивно (`register_document_extractor`). Существующие
плагины не менялись; `ExtractorRegistry` / ingestion / Agent — без правок под
плагин. Typed `register_*` остаётся осознанным дублированием.

**Plugin API Status:** Proven for Tool, ContextLayer and DocumentExtractor.
Further evolution requires new extension categories or demonstrated limitations
of the current API.

Четвёртую ось искусственно не ищем (ещё один Tool/Layer/Extractor — не новая
категория; Ranker/Embedding — скорее DI/composition root). PluginLoader и
generic registry не вводятся без нового факта. Следующий крупный этап Phase 2 —
Streaming.

## Стратегический цикл Phase 2

```
гипотеза → два независимых подтверждения → оценка API → следующая ось
```

#27 lifecycle, #28 Tool, #30 ContextLayer, этот review — середина цикла.
После третьей оси имеет смысл снова спросить: нужен ли loader / нужен ли
более общий registry. Не раньше.
