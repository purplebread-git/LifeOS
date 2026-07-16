"""KnowledgeContextLayer — заглушка под будущий Knowledge Base / RAG.

Сейчас контекст не меняется. Когда появится KnowledgeProvider (контракт
уже есть в app/core/knowledge_provider.py), слой начнёт искать релевантные
знания и добавлять их — без изменения LayeredContextBuilder и остального
pipeline.
"""

from __future__ import annotations

from app.core.context_layer import ContextLayer
from app.models.conversation import Conversation
from app.models.message import Message


class KnowledgeContextLayer(ContextLayer):
    async def apply(
        self,
        conversation: Conversation,
        context: list[Message],
    ) -> list[Message]:
        return context
