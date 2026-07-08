# LifeOS Agent — Roadmap

- [x] Foundation
- [x] Core interfaces (ABC)
- [x] DI Container (dependency-injector)
- [x] OpenAIProvider (+ нормализация: mapper, TypedDict, SecretStr, exceptions)
- [x] ConversationRepository + InMemoryConversationRepository
- [x] Real Agent (SimpleAgent, stubs.py удалён)
- [ ] ToolManager — инфраструктура диспетчеризации (без ReAct-цикла)
- [ ] Real ConversationEngine (ReAct-цикл: интеграция ToolManager)
- [ ] Production MemoryProvider
- [ ] Plugins (реальные интеграции)
- [ ] Streaming
- [ ] Observability
- [ ] MCP
- [ ] Multi-agent
- [ ] Web UI

## Известные архитектурные натяжения (не баги, но требуют решения позже)

1. **AgentResponse vs Conversation.** `AgentResponse.messages` содержит
   только новый ответ ассистента, в то время как `Conversation.messages`
   уже хранит полную историю. Это два разных представления одного
   разговора. Решать вместе с дизайном `api/` — не раньше.
2. **Mutable Conversation.** `ConversationRepository.get_by_id()` отдаёт
   mutable-объект, который затем мутирует `ConversationEngine`. Работает,
   но если понадобится многопоточный/многопроцессный доступ к одному
   разговору — потребуется либо immutable-модель + explicit save,
   либо блокировки на уровне репозитория.
3. 
## Согласованный контракт следующей итерации (ToolManager)

```python
class ToolManager(ABC):
    @abstractmethod
    def tool_definitions(self) -> list[ToolDefinition]: ...

    @abstractmethod
    async def execute(self, tool_call: ToolCall, context: ExecutionContext) -> ToolResult: ...
```

Правило обработки ошибок: execute() ловит только ToolExecutionError и
превращает в ToolResult(is_error=True, ...). Прочие исключения (баги в
коде инструмента) пробрасываются дальше — не маскируются.

Итерация строит ТОЛЬКО диспетчер (definitions + execute по имени).
Без ReAct-цикла, без интеграции в ConversationEngine — это отдельная
итерация после.