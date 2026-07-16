"""KnowledgeContextLayer — инъекция релевантных знаний в контекст.

Ищет знания по последнему USER-сообщению (тот же принцип, что у памяти:
не искать по tool-выводам в ReAct-цикле) и добавляет их отдельным
system-сообщением с атрибуцией источника. Без KnowledgeProvider или при
пустом результате контекст не меняется.

Хелперы _last_user_message/_extract_text намеренно продублированы из
memory_context_layer, а не импортированы: связывать подсистемы знаний и
памяти ради двух строк нежелательно.
"""

from __future__ import annotations

from app.core.context_layer import ContextLayer
from app.core.knowledge_provider import KnowledgeProvider
from app.models.conversation import Conversation
from app.models.knowledge import KnowledgeChunk
from app.models.message import Message, Role, TextBlock

DEFAULT_KNOWLEDGE_TOP_K = 5

_KNOWLEDGE_SYSTEM_INSTRUCTION = (
    "The following knowledge may be relevant.\n"
    "Use it only if it helps answer the user's message.\n"
    "\n"
)


class KnowledgeContextLayer(ContextLayer):
    def __init__(
        self,
        knowledge_provider: KnowledgeProvider | None = None,
        top_k: int = DEFAULT_KNOWLEDGE_TOP_K,
    ) -> None:
        self._knowledge_provider = knowledge_provider
        self._top_k = top_k

    async def apply(
        self,
        conversation: Conversation,
        context: list[Message],
    ) -> list[Message]:
        chunks = await self._resolve_chunks(conversation)
        if not chunks:
            return context
        return [*context, self._knowledge_system_message(chunks)]

    async def _resolve_chunks(self, conversation: Conversation) -> list[KnowledgeChunk]:
        if self._knowledge_provider is None:
            return []

        user_message = _last_user_message(conversation)
        if user_message is None:
            return []

        query = _extract_text(user_message)
        if not query:
            return []

        return await self._knowledge_provider.search(query, limit=self._top_k)

    @staticmethod
    def _knowledge_system_message(chunks: list[KnowledgeChunk]) -> Message:
        lines = "\n".join(f"- {chunk.content} (source: {chunk.source})" for chunk in chunks)
        return Message(
            role=Role.SYSTEM,
            content=[TextBlock(text=f"{_KNOWLEDGE_SYSTEM_INSTRUCTION}{lines}")],
        )


def _last_user_message(conversation: Conversation) -> Message | None:
    for message in reversed(conversation.messages):
        if message.role == Role.USER:
            return message
    return None


def _extract_text(message: Message) -> str:
    parts = [block.text for block in message.content if isinstance(block, TextBlock)]
    return " ".join(parts).strip()
