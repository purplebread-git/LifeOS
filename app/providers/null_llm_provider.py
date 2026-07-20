"""NullLLMProvider — детерминированная реализация LLMProvider.

Не делает сетевых запросов.
Используется для проверки DI-графа и тестов.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from app.core.llm_provider import LLMProvider
from app.models import (
    LLMResponse,
    Message,
    Role,
    TextBlock,
    ToolDefinition,
)

_NULL_REPLY = "[NullLLMProvider] заглушка ответа"


class NullLLMProvider(LLMProvider):
    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> LLMResponse:
        return LLMResponse(
            message=Message(
                role=Role.ASSISTANT,
                content=[
                    TextBlock(
                        text=_NULL_REPLY,
                    )
                ],
            ),
            finish_reason="stop",
        )

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> AsyncIterator[str]:
        if tools is not None:
            raise NotImplementedError("Streaming with tools is not supported yet")
        yield _NULL_REPLY
