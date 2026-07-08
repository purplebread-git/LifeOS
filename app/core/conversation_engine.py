from abc import ABC, abstractmethod

from app.models.conversation import Conversation
from app.models.message import Message


class ConversationEngine(ABC):
    @abstractmethod
    async def run_turn(self, conversation: Conversation, user_message: Message) -> Message:
        raise NotImplementedError
