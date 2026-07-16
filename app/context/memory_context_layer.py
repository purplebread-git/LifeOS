"""MemoryContextLayer — инъекция релевантной памяти в контекст.

Ищет воспоминания по последнему USER-сообщению и добавляет их отдельным
system-сообщением. Логика перенесена из SimpleContextBuilder без изменения
поведения. Без MemoryProvider или при пустом результате контекст не
меняется.
"""

from __future__ import annotations

from app.core.context_layer import ContextLayer
from app.core.memory_provider import MemoryProvider
from app.models.conversation import Conversation
from app.models.memory import MemoryEntry
from app.models.message import Message, Role, TextBlock

DEFAULT_MEMORY_TOP_K = 5

# Ключ для кэша результатов поиска памяти внутри одного turn.
# Сейчас никто не записывает это значение; слой читает его, если есть.
# В будущем ConversationEngine сможет заполнить metadata один раз до
# ReAct-цикла — повторные build() перестанут вызывать search().
#
# TODO: When turn-scoped caching becomes active, consider moving cache
# ownership into ConversationEngine instead of reading Conversation.metadata
# directly. metadata must not survive repository save/load across turns.
MEMORY_CONTEXT_METADATA_KEY = "memory_context"

_MEMORY_SYSTEM_INSTRUCTION = (
    "The following memories from past interactions may be relevant.\n"
    "Use them only if they help answer the user's message.\n"
    "\n"
)


class MemoryContextLayer(ContextLayer):
    def __init__(
        self,
        memory_provider: MemoryProvider | None = None,
        top_k: int = DEFAULT_MEMORY_TOP_K,
    ) -> None:
        self._memory_provider = memory_provider
        self._top_k = top_k

    async def apply(
        self,
        conversation: Conversation,
        context: list[Message],
    ) -> list[Message]:
        memories = await self._resolve_memory_entries(conversation)
        if not memories:
            return context
        return [*context, self._memory_system_message(memories)]

    async def _resolve_memory_entries(self, conversation: Conversation) -> list[MemoryEntry]:
        if self._memory_provider is None:
            return []

        cached = conversation.metadata.get(MEMORY_CONTEXT_METADATA_KEY)
        if isinstance(cached, list) and all(isinstance(entry, MemoryEntry) for entry in cached):
            return cached

        user_message = _last_user_message(conversation)
        if user_message is None:
            return []

        query = _extract_text(user_message)
        if not query:
            return []

        return await self._memory_provider.search(query, limit=self._top_k)

    @staticmethod
    def _memory_system_message(memories: list[MemoryEntry]) -> Message:
        lines = "\n".join(f"- {memory.content}" for memory in memories)
        return Message(
            role=Role.SYSTEM,
            content=[TextBlock(text=f"{_MEMORY_SYSTEM_INSTRUCTION}{lines}")],
        )


def _last_user_message(conversation: Conversation) -> Message | None:
    for message in reversed(conversation.messages):
        if message.role == Role.USER:
            return message
    return None


def _extract_text(message: Message) -> str:
    parts = [block.text for block in message.content if isinstance(block, TextBlock)]
    return " ".join(parts).strip()
