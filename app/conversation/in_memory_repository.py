"""InMemoryConversationRepository — хранение Conversation в памяти процесса.

Гарантирует инвариант: "получил разговор через get_by_id()" == "он уже
существует в хранилище". Новый Conversation сохраняется сразу при первом
обращении — иначе вызывающий код мог бы получить объект, изменить его и
забыть вызвать save(), потеряв изменения при следующем get_by_id().

Не переживает перезапуск процесса; годится для разработки и тестов.
"""

from __future__ import annotations

from app.core.conversation_repository import ConversationRepository
from app.models.conversation import Conversation


class InMemoryConversationRepository(ConversationRepository):
    def __init__(self) -> None:
        self._storage: dict[str, Conversation] = {}

    async def get_by_id(self, conversation_id: str) -> Conversation:
        if conversation_id not in self._storage:
            self._storage[conversation_id] = Conversation(conversation_id=conversation_id)
        return self._storage[conversation_id]

    async def save(self, conversation: Conversation) -> None:
        """Для in-memory реализации это фактически no-op (объект и так тот
        же самый в _storage), но метод сохранён как часть контракта
        ConversationRepository — production-реализации (SQLAlchemy и т.п.)
        будут реально писать в БД здесь."""
        self._storage[conversation.conversation_id] = conversation
