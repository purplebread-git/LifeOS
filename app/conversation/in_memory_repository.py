"""InMemoryConversationRepository — хранение Conversation в памяти процесса."""

from __future__ import annotations

from app.core.conversation_repository import ConversationRepository
from app.models.conversation import Conversation


class InMemoryConversationRepository(ConversationRepository):
    def __init__(self) -> None:
        self._storage: dict[str, Conversation] = {}

    async def load(self, conversation_id: str) -> Conversation:
        if conversation_id not in self._storage:
            self._storage[conversation_id] = Conversation(
                conversation_id=conversation_id,
            )
        return self._storage[conversation_id]

    async def save(self, conversation: Conversation) -> None:
        self._storage[conversation.conversation_id] = conversation
