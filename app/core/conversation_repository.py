"""Контракт хранения Conversation."""

from abc import ABC, abstractmethod

from app.models.conversation import Conversation


class ConversationRepository(ABC):
    @abstractmethod
    async def load(self, conversation_id: str) -> Conversation:
        """Вернуть существующий Conversation или создать новый с этим id.

        Реализация отвечает за то, чтобы повторный load() с тем же id
        отражал все изменения, сохранённые через save() ранее.
        """
        raise NotImplementedError

    @abstractmethod
    async def save(self, conversation: Conversation) -> None:
        raise NotImplementedError
