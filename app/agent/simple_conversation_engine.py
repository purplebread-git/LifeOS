"""SimpleConversationEngine — логика одного шага диалога без tool calling.

ВАЖНО: run_turn() / stream_turn() мутируют переданный объект Conversation —
добавляют в conversation.messages и сообщение пользователя, и ответ модели.
Сохранение изменений в хранилище — не забота этого класса, этим занимается
Agent через ConversationRepository.save().

Цикл вызова инструментов — в ToolConversationEngine.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from app.core.context_builder import ContextBuilder
from app.core.conversation_engine import ConversationEngine
from app.core.llm_provider import LLMProvider
from app.models.conversation import Conversation
from app.models.message import Message, Role, TextBlock


class SimpleConversationEngine(ConversationEngine):
    def __init__(self, llm_provider: LLMProvider, context_builder: ContextBuilder) -> None:
        self._llm_provider = llm_provider
        self._context_builder = context_builder

    async def run_turn(self, conversation: Conversation, user_message: Message) -> Message:
        # Побочный эффект: мутируем conversation.messages напрямую.
        conversation.messages.append(user_message)

        context = await self._context_builder.build(conversation)
        response = await self._llm_provider.generate(context)

        conversation.messages.append(response.message)

        return response.message

    async def stream_turn(
        self,
        conversation: Conversation,
        user_message: Message,
    ) -> AsyncIterator[str]:
        conversation.messages.append(user_message)

        context = await self._context_builder.build(conversation)
        parts: list[str] = []
        async for token in self._llm_provider.stream(context):
            parts.append(token)
            yield token

        assistant_message = Message(
            role=Role.ASSISTANT,
            content=[TextBlock(text="".join(parts))],
        )
        conversation.messages.append(assistant_message)
