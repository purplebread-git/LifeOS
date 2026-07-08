"""NullLLMProvider — детерминированная реализация LLMProvider.

Не делает сетевых запросов.
Используется для проверки DI-графа и тестов.
"""

from __future__ import annotations

from app.core.llm_provider import LLMProvider
from app.models import (
    LLMResponse,
    Message,
    Role,
    TextBlock,
    ToolDefinition,
)


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
                        text="[NullLLMProvider] заглушка ответа",
                    )
                ],
            ),
            finish_reason="stop",
        )
