from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.models.conversation import AgentResponse


class Agent(ABC):
    @abstractmethod
    async def respond(self, conversation_id: str, user_input: str) -> AgentResponse:
        raise NotImplementedError

    @abstractmethod
    def stream_respond(
        self,
        conversation_id: str,
        user_input: str,
    ) -> AsyncIterator[str]:
        """Тот же turn, что respond(), но текст отдаётся потоком.

        Семантика выполнения — ConversationEngine.stream_turn (один ReAct).
        """
        raise NotImplementedError
