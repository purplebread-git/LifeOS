"""SimpleAgent — реализация Agent, владеющая жизненным циклом разговора.

Поток: получить Conversation → отдать в ConversationEngine вместе с
сообщением пользователя → сохранить обновлённый Conversation → вернуть
ответ. Именно Agent, а не ConversationEngine и не ToolManager, отвечает за
загрузку и сохранение истории.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from app.core.agent import Agent
from app.core.conversation_engine import ConversationEngine
from app.core.conversation_repository import ConversationRepository
from app.models.conversation import AgentResponse
from app.models.message import Message, Role, TextBlock


class SimpleAgent(Agent):
    def __init__(
        self,
        conversation_engine: ConversationEngine,
        conversation_repository: ConversationRepository,
    ) -> None:
        self._conversation_engine = conversation_engine
        self._conversation_repository = conversation_repository

    async def respond(self, conversation_id: str, user_input: str) -> AgentResponse:
        conversation = await self._conversation_repository.load(conversation_id)
        user_message = Message(
            role=Role.USER,
            content=[TextBlock(text=user_input)],
        )

        reply = await self._conversation_engine.run_turn(conversation, user_message)

        await self._conversation_repository.save(conversation)

        return AgentResponse(conversation_id=conversation_id, messages=[reply])

    async def stream_respond(
        self,
        conversation_id: str,
        user_input: str,
    ) -> AsyncIterator[str]:
        conversation = await self._conversation_repository.load(conversation_id)
        user_message = Message(
            role=Role.USER,
            content=[TextBlock(text=user_input)],
        )

        async for token in self._conversation_engine.stream_turn(conversation, user_message):
            yield token

        await self._conversation_repository.save(conversation)
