"""SimpleContextBuilder — reference-реализация ContextBuilder.

Возвращает копию истории сообщений разговора — вызывающий код не должен
случайно мутировать conversation.messages через результат build().
Обогащение контекста (память, знания, системный промпт) собирается через
LayeredContextBuilder из app/context/. Этот builder остаётся минимальным
эталоном и удобен для локальных тестов простого пути (SimpleConversationEngine).
"""

from __future__ import annotations

from app.core.context_builder import ContextBuilder
from app.models.conversation import Conversation
from app.models.message import Message


class SimpleContextBuilder(ContextBuilder):
    async def build(self, conversation: Conversation) -> list[Message]:
        return conversation.messages.copy()
