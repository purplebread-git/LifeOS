"""LayeredContextBuilder — сборка контекста как pipeline из ContextLayer.

Слои применяются по порядку; каждый получает накопленный контекст и
возвращает новый. Порядок задаётся в composition root (Container).
Добавление нового слоя (например, Knowledge/RAG) не меняет builder.
"""

from __future__ import annotations

from app.core.context_builder import ContextBuilder
from app.core.context_layer import ContextLayer
from app.models.conversation import Conversation
from app.models.message import Message


class LayeredContextBuilder(ContextBuilder):
    def __init__(self, layers: list[ContextLayer]) -> None:
        self._layers = layers

    async def build(self, conversation: Conversation) -> list[Message]:
        context: list[Message] = []
        for layer in self._layers:
            context = await layer.apply(conversation, context)
        return context
