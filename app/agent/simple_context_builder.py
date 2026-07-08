"""SimpleContextBuilder — минимальная реализация ContextBuilder.

Возвращает копию истории сообщений разговора — вызывающий код не должен
случайно мутировать conversation.messages через результат build().
Более сложная логика (обрезка по токенам, инъекция памяти) появится
позже без изменения сигнатуры build().
"""
from __future__ import annotations

from app.core.context_builder import ContextBuilder
from app.models.conversation import Conversation
from app.models.message import Message


class SimpleContextBuilder(ContextBuilder):
    async def build(self, conversation: Conversation) -> list[Message]:
        return conversation.messages.copy()