from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.models.conversation import Conversation
from app.models.message import Message


class ConversationEngine(ABC):
    @abstractmethod
    async def run_turn(self, conversation: Conversation, user_message: Message) -> Message:
        raise NotImplementedError

    @abstractmethod
    def stream_turn(
        self,
        conversation: Conversation,
        user_message: Message,
    ) -> AsyncIterator[str]:
        """Потоковый ход: те же side-effects на Conversation, что run_turn.

        Streaming — альтернативный транспорт результата, а не альтернативный
        режим выполнения агента. Наружу только текст; tool events не стримятся.
        """
        raise NotImplementedError
