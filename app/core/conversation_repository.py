"""Контракт хранения Conversation.

Только интерфейс.
Конкретная реализация появится вместе с настоящим Agent.

Repository не обязан создавать объект при отсутствии записи:
создание Conversation — ответственность вызывающего слоя.
"""

from abc import ABC, abstractmethod

from app.models.conversation import Conversation


class ConversationRepository(ABC):
    @abstractmethod
    async def get(
        self,
        conversation_id: str,
    ) -> Conversation | None:
        """Получить существующий разговор."""
        raise NotImplementedError

    @abstractmethod
    async def save(
        self,
        conversation: Conversation,
    ) -> None:
        """Сохранить разговор."""
        raise NotImplementedError