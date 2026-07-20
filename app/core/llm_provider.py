from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.models.message import LLMResponse, Message
from app.models.tool import ToolDefinition


class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> LLMResponse:
        raise NotImplementedError

    @abstractmethod
    def stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> AsyncIterator[str]:
        """Поток текстовых дельт. Семантика ответа та же, что у generate().

        Streaming меняет только способ доставки, не результат. tools в этом
        контракте зарезервированы; поддержка streaming tool calls — отдельный PR.
        """
        raise NotImplementedError
