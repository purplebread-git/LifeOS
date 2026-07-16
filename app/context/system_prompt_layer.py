"""SystemPromptLayer — добавляет системный промпт (персона/инструкции).

Пустой промпт → слой ничего не добавляет.
"""

from __future__ import annotations

from app.core.context_layer import ContextLayer
from app.models.conversation import Conversation
from app.models.message import Message, Role, TextBlock


class SystemPromptLayer(ContextLayer):
    def __init__(self, system_prompt: str) -> None:
        self._system_prompt = system_prompt

    async def apply(
        self,
        conversation: Conversation,
        context: list[Message],
    ) -> list[Message]:
        if not self._system_prompt.strip():
            return context

        system_message = Message(
            role=Role.SYSTEM,
            content=[TextBlock(text=self._system_prompt)],
        )
        return [*context, system_message]
