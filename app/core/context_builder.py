from abc import ABC, abstractmethod

from app.models.conversation import Conversation
from app.models.message import Message


class ContextBuilder(ABC):
    @abstractmethod
    async def build(self, conversation: Conversation) -> list[Message]:
        raise NotImplementedError