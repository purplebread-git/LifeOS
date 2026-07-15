from typing import cast

from app.agent.simple_context_builder import (
    DEFAULT_MEMORY_TOP_K,
    MEMORY_CONTEXT_METADATA_KEY,
    SimpleContextBuilder,
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


def _system_text(messages: list[Message]) -> str | None:
    if not messages or messages[0].role != Role.SYSTEM:
        return None
    block = messages[0].content[0]
    assert isinstance(block, TextBlock)
    return block.text


async def test_memory_injected_into_context() -> None:
    memory = InMemoryMemoryProvider()
    await memory.add(MemoryEntry(id="1", content="User height is 171 cm"))

    builder = SimpleContextBuilder(memory_provider=memory)
    conversation = Conversation(
        conversation_id="conv-1",
        messages=[
            Message(role=Role.USER, content=[TextBlock(text="height")]),
        ],
    )

    context = await builder.build(conversation)

    system_text = _system_text(context)
    assert system_text is not None
    assert "may be relevant" in system_text
    assert "Use them only if they help" in system_text
    assert "- User height is 171 cm" in system_text
    assert len(context) == 2
    assert context[1].role == Role.USER


async def test_no_memories_found_returns_conversation_only() -> None:
    memory = InMemoryMemoryProvider()
    builder = SimpleContextBuilder(memory_provider=memory)
    conversation = Conversation(
        conversation_id="conv-1",
        messages=[
            Message(role=Role.USER, content=[TextBlock(text="Tell me about me")]),
        ],
    )

    context = await builder.build(conversation)

    assert len(context) == 1
    assert context[0].role == Role.USER


async def test_no_memory_provider_behaves_like_plain_copy() -> None:
    builder = SimpleContextBuilder()
    conversation = Conversation(
        conversation_id="conv-1",
        messages=[
            Message(role=Role.USER, content=[TextBlock(text="Hello")]),
            Message(role=Role.ASSISTANT, content=[TextBlock(text="Hi")]),
        ],
    )

    context = await builder.build(conversation)

    assert len(context) == 2
    assert context[0].role == Role.USER
    assert context[1].role == Role.ASSISTANT


async def test_top_k_limits_injected_memories() -> None:
    memory = InMemoryMemoryProvider()
    for index in range(10):
        await memory.add(MemoryEntry(id=str(index), content=f"color purple {index}"))

    builder = SimpleContextBuilder(memory_provider=memory, top_k=2)
    conversation = Conversation(
        conversation_id="conv-1",
        messages=[
            Message(role=Role.USER, content=[TextBlock(text="purple")]),
        ],
    )

    context = await builder.build(conversation)
    system_text = cast(str, _system_text(context))

    assert system_text.count("- color purple") == 2


async def test_memory_search_uses_last_user_not_last_message() -> None:
    memory = InMemoryMemoryProvider()
    await memory.add(MemoryEntry(id="1", content="User height is 171 cm"))

    builder = SimpleContextBuilder(memory_provider=memory)
    conversation = Conversation(
        conversation_id="conv-1",
        messages=[
            Message(role=Role.USER, content=[TextBlock(text="height")]),
            Message(role=Role.TOOL, content=[TextBlock(text="tool output should not be searched")]),
            Message(role=Role.ASSISTANT, content=[TextBlock(text="Checking...")]),
        ],
    )

    context = await builder.build(conversation)
    system_text = cast(str, _system_text(context))

    assert "- User height is 171 cm" in system_text
    assert "tool output should not be searched" not in system_text


async def test_metadata_cache_skips_repeated_search() -> None:
    delegate = InMemoryMemoryProvider()
    await delegate.add(MemoryEntry(id="1", content="User height is 171 cm"))
    memory = _CountingMemoryProvider(delegate)

    builder = SimpleContextBuilder(memory_provider=memory)
    cached_entry = MemoryEntry(id="cached", content="Cached memory")
    conversation = Conversation(
        conversation_id="conv-1",
        messages=[
            Message(role=Role.USER, content=[TextBlock(text="height")]),
        ],
        metadata={MEMORY_CONTEXT_METADATA_KEY: [cached_entry]},
    )

    first = await builder.build(conversation)
    second = await builder.build(conversation)

    assert memory.search_calls == 0
    system_text = cast(str, _system_text(first))
    assert "- Cached memory" in system_text
    assert _system_text(second) == system_text


async def test_default_top_k_matches_constant() -> None:
    memory = InMemoryMemoryProvider()
    for index in range(DEFAULT_MEMORY_TOP_K + 3):
        await memory.add(MemoryEntry(id=str(index), content=f"topic alpha {index}"))

    builder = SimpleContextBuilder(memory_provider=memory)
    conversation = Conversation(
        conversation_id="conv-1",
        messages=[
            Message(role=Role.USER, content=[TextBlock(text="alpha")]),
        ],
    )

    context = await builder.build(conversation)
    system_text = cast(str, _system_text(context))

    assert system_text.count("- topic alpha") == DEFAULT_MEMORY_TOP_K
