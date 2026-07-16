"""ConversationHistoryLayer — добавляет историю сообщений разговора.

Копия conversation.messages: вызывающий код не должен мутировать историю
через результат build().
"""

from __future__ import annotations

from app.core.context_layer import ContextLayer
from app.models.conversation import Conversation
from app.models.message import Message


class ConversationHistoryLayer(ContextLayer):
    async def apply(
        self,
        conversation: Conversation,
        context: list[Message],
    ) -> list[Message]:
        return [*context, *conversation.messages]
