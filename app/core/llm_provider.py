from abc import ABC, abstractmethod

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
