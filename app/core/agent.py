from abc import ABC, abstractmethod

from app.models.conversation import AgentResponse


class Agent(ABC):
    @abstractmethod
    async def respond(self, conversation_id: str, user_input: str) -> AgentResponse:
        raise NotImplementedError