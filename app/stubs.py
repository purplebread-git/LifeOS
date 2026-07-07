"""ВРЕМЕННЫЕ заглушки для проверки сборки Container (Итерация 3).

Эти классы НЕ являются финальными реализациями — заменяются в Итерациях
5-6 (ToolManager, полноценный Agent).

ИЗВЕСТНОЕ ОГРАНИЧЕНИЕ: StubAgent создаёт новый Conversation() на каждый
вызов respond() — conversation_id пока не связан с реально сохранённой
историей. Это осознанно оставлено как есть до появления
ConversationRepository (см. core/conversation_repository.py) и настоящего
Agent в Итерации 6/7, а не архитектурная ошибка текущей итерации.
"""

from __future__ import annotations

from app.core.agent import Agent
from app.core.context_builder import ContextBuilder
from app.core.conversation_engine import ConversationEngine
from app.core.llm_provider import LLMProvider
from app.core.memory_provider import MemoryProvider
from app.models.conversation import AgentResponse, Conversation
from app.models.message import Message, Role


class StubContextBuilder(ContextBuilder):
    async def build(self, conversation: Conversation) -> list[Message]:
        return list(conversation.messages)


class StubConversationEngine(ConversationEngine):
    def __init__(self, llm_provider: LLMProvider, context_builder: ContextBuilder) -> None:
        self._llm_provider = llm_provider
        self._context_builder = context_builder

    async def run_turn(self, conversation: Conversation, user_message: Message) -> Message:
        conversation.messages.append(user_message)
        context = await self._context_builder.build(conversation)
        response = await self._llm_provider.generate(context)
        return response.message


class StubAgent(Agent):
    def __init__(self, conversation_engine: ConversationEngine, memory_provider: MemoryProvider) -> None:
        self._conversation_engine = conversation_engine
        self._memory_provider = memory_provider

    async def respond(self, conversation_id: str, user_input: str) -> AgentResponse:
        conversation = Conversation(conversation_id=conversation_id)
        user_message = Message(role=Role.USER, content=user_input)
        reply = await self._conversation_engine.run_turn(conversation, user_message)
        return AgentResponse(conversation_id=conversation_id, messages=[reply])