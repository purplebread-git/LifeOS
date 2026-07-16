from typing import cast

from app.context.knowledge_context_layer import (
    DEFAULT_KNOWLEDGE_TOP_K,
    KnowledgeContextLayer,
)
from app.knowledge.in_memory_knowledge_provider import InMemoryKnowledgeProvider
from app.models.conversation import Conversation
from app.models.knowledge import KnowledgeChunk
from app.models.message import Message, Role, TextBlock


def _knowledge_message(messages: list[Message]) -> str | None:
    for message in messages:
        if message.role != Role.SYSTEM:
            continue
        block = message.content[0]
        assert isinstance(block, TextBlock)
        if "knowledge may be relevant" in block.text:
            return block.text
    return None


def _conversation(text: str) -> Conversation:
    return Conversation(
        conversation_id="conv-1",
        messages=[Message(role=Role.USER, content=[TextBlock(text=text)])],
    )


async def test_knowledge_injected_end_to_end() -> None:
    # Acceptance-тест PR: knowledge added → user asks → layer injects chunk.
    # Именно это доказывает Knowledge → Context. Substring-MVP требует, чтобы
    # запрос содержался в чанке (то же ограничение, что у памяти); семантика,
    # понимающая полный вопрос, придёт отдельным шагом.
    knowledge = InMemoryKnowledgeProvider()
    await knowledge.add(
        KnowledgeChunk(
            id="1",
            content="LifeOS is a modular agent platform for building assistants",
            source="handbook",
        )
    )

    layer = KnowledgeContextLayer(knowledge_provider=knowledge)
    result = await layer.apply(_conversation("modular agent platform"), [])

    text = _knowledge_message(result)
    assert text is not None
    assert "knowledge may be relevant" in text
    assert "modular agent platform for building assistants (source: handbook)" in text


async def test_knowledge_preserves_incoming_context() -> None:
    knowledge = InMemoryKnowledgeProvider()
    await knowledge.add(KnowledgeChunk(id="1", content="fact about python", source="doc"))

    incoming = [Message(role=Role.SYSTEM, content=[TextBlock(text="persona")])]
    layer = KnowledgeContextLayer(knowledge_provider=knowledge)
    result = await layer.apply(_conversation("python"), incoming)

    assert result[0].content[0].text == "persona"  # type: ignore[union-attr]
    assert len(result) == 2


async def test_no_knowledge_found_returns_context_unchanged() -> None:
    knowledge = InMemoryKnowledgeProvider()
    layer = KnowledgeContextLayer(knowledge_provider=knowledge)

    result = await layer.apply(_conversation("nothing matches"), [])

    assert result == []


async def test_no_knowledge_provider_is_passthrough() -> None:
    layer = KnowledgeContextLayer()
    incoming = [Message(role=Role.USER, content=[TextBlock(text="hi")])]

    result = await layer.apply(_conversation("hi"), incoming)

    assert result == incoming


async def test_top_k_limits_injected_chunks() -> None:
    knowledge = InMemoryKnowledgeProvider()
    await knowledge.add_batch(
        [KnowledgeChunk(id=str(i), content=f"topic purple {i}", source="s") for i in range(10)]
    )

    layer = KnowledgeContextLayer(knowledge_provider=knowledge, top_k=2)
    result = await layer.apply(_conversation("purple"), [])

    text = cast(str, _knowledge_message(result))
    assert text.count("- topic purple") == 2


async def test_search_uses_last_user_not_tool_output() -> None:
    knowledge = InMemoryKnowledgeProvider()
    await knowledge.add(KnowledgeChunk(id="1", content="paris facts", source="doc"))

    conversation = Conversation(
        conversation_id="conv-1",
        messages=[
            Message(role=Role.USER, content=[TextBlock(text="paris")]),
            Message(role=Role.TOOL, content=[TextBlock(text="tool output must not be searched")]),
            Message(role=Role.ASSISTANT, content=[TextBlock(text="Checking...")]),
        ],
    )

    layer = KnowledgeContextLayer(knowledge_provider=knowledge)
    result = await layer.apply(conversation, [])

    text = cast(str, _knowledge_message(result))
    assert "- paris facts (source: doc)" in text
    assert "tool output must not be searched" not in text


async def test_default_top_k_matches_constant() -> None:
    knowledge = InMemoryKnowledgeProvider()
    await knowledge.add_batch(
        [
            KnowledgeChunk(id=str(i), content=f"topic alpha {i}", source="s")
            for i in range(DEFAULT_KNOWLEDGE_TOP_K + 3)
        ]
    )

    layer = KnowledgeContextLayer(knowledge_provider=knowledge)
    result = await layer.apply(_conversation("alpha"), [])

    text = cast(str, _knowledge_message(result))
    assert text.count("- topic alpha") == DEFAULT_KNOWLEDGE_TOP_K
