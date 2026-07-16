from typing import cast

from app.context.memory_context_layer import (
    DEFAULT_MEMORY_TOP_K,
    MEMORY_CONTEXT_METADATA_KEY,
    MemoryContextLayer,
)
from app.core.memory_provider import MemoryProvider
from app.memory.in_memory_provider import InMemoryMemoryProvider
from app.models.conversation import Conversation
from app.models.memory import MemoryEntry
from app.models.message import Message, Role, TextBlock


class _CountingMemoryProvider(MemoryProvider):
    def __init__(self, delegate: InMemoryMemoryProvider) -> None:
        self._delegate = delegate
        self.search_calls = 0

    async def add(self, entry: MemoryEntry) -> None:
        await self._delegate.add(entry)

    async def get(self, entry_id: str) -> MemoryEntry | None:
        return await self._delegate.get(entry_id)

    async def update(self, entry: MemoryEntry) -> None:
        await self._delegate.update(entry)

    async def delete(self, entry_id: str) -> None:
        await self._delegate.delete(entry_id)

    async def search(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        self.search_calls += 1
        return await self._delegate.search(query, limit=limit)


def _memory_message(messages: list[Message]) -> str | None:
    for message in messages:
        if message.role != Role.SYSTEM:
            continue
        block = message.content[0]
        assert isinstance(block, TextBlock)
        if "may be relevant" in block.text:
            return block.text
    return None


def _conversation(text: str) -> Conversation:
    return Conversation(
        conversation_id="conv-1",
        messages=[Message(role=Role.USER, content=[TextBlock(text=text)])],
    )


async def test_memory_appended_to_context() -> None:
    memory = InMemoryMemoryProvider()
    await memory.add(MemoryEntry(id="1", content="User height is 171 cm"))

    layer = MemoryContextLayer(memory_provider=memory)
    result = await layer.apply(_conversation("height"), [])

    text = _memory_message(result)
    assert text is not None
    assert "may be relevant" in text
    assert "Use them only if they help" in text
    assert "- User height is 171 cm" in text


async def test_memory_preserves_incoming_context() -> None:
    memory = InMemoryMemoryProvider()
    await memory.add(MemoryEntry(id="1", content="User height is 171 cm"))

    incoming = [Message(role=Role.SYSTEM, content=[TextBlock(text="persona")])]
    layer = MemoryContextLayer(memory_provider=memory)
    result = await layer.apply(_conversation("height"), incoming)

    assert result[0].content[0].text == "persona"  # type: ignore[union-attr]
    assert len(result) == 2


async def test_no_memories_found_returns_context_unchanged() -> None:
    memory = InMemoryMemoryProvider()
    layer = MemoryContextLayer(memory_provider=memory)

    result = await layer.apply(_conversation("nothing matches"), [])

    assert result == []


async def test_no_memory_provider_is_passthrough() -> None:
    layer = MemoryContextLayer()
    incoming = [Message(role=Role.USER, content=[TextBlock(text="hi")])]

    result = await layer.apply(_conversation("hi"), incoming)

    assert result == incoming


async def test_top_k_limits_injected_memories() -> None:
    memory = InMemoryMemoryProvider()
    for index in range(10):
        await memory.add(MemoryEntry(id=str(index), content=f"color purple {index}"))

    layer = MemoryContextLayer(memory_provider=memory, top_k=2)
    result = await layer.apply(_conversation("purple"), [])

    text = cast(str, _memory_message(result))
    assert text.count("- color purple") == 2


async def test_memory_search_uses_last_user_not_last_message() -> None:
    memory = InMemoryMemoryProvider()
    await memory.add(MemoryEntry(id="1", content="height 171"))

    conversation = Conversation(
        conversation_id="conv-1",
        messages=[
            Message(role=Role.USER, content=[TextBlock(text="height")]),
            Message(role=Role.TOOL, content=[TextBlock(text="tool output must not be searched")]),
            Message(role=Role.ASSISTANT, content=[TextBlock(text="Checking...")]),
        ],
    )

    layer = MemoryContextLayer(memory_provider=memory)
    result = await layer.apply(conversation, [])

    text = cast(str, _memory_message(result))
    assert "- height 171" in text
    assert "tool output must not be searched" not in text


async def test_metadata_cache_skips_repeated_search() -> None:
    delegate = InMemoryMemoryProvider()
    await delegate.add(MemoryEntry(id="1", content="height 171"))
    memory = _CountingMemoryProvider(delegate)

    cached_entry = MemoryEntry(id="cached", content="Cached memory")
    conversation = Conversation(
        conversation_id="conv-1",
        messages=[Message(role=Role.USER, content=[TextBlock(text="height")])],
        metadata={MEMORY_CONTEXT_METADATA_KEY: [cached_entry]},
    )

    layer = MemoryContextLayer(memory_provider=memory)
    result = await layer.apply(conversation, [])

    assert memory.search_calls == 0
    assert "- Cached memory" in cast(str, _memory_message(result))


async def test_default_top_k_matches_constant() -> None:
    memory = InMemoryMemoryProvider()
    for index in range(DEFAULT_MEMORY_TOP_K + 3):
        await memory.add(MemoryEntry(id=str(index), content=f"topic alpha {index}"))

    layer = MemoryContextLayer(memory_provider=memory)
    result = await layer.apply(_conversation("alpha"), [])

    text = cast(str, _memory_message(result))
    assert text.count("- topic alpha") == DEFAULT_MEMORY_TOP_K
