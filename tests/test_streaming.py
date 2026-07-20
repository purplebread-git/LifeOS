"""Streaming — только транспорт. Семантика ответа = generate().

Инвариант: ''.join(stream_tokens) == text из generate().message
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import pytest

from app.agent import SimpleContextBuilder, SimpleConversationEngine
from app.core.llm_provider import LLMProvider
from app.models.conversation import Conversation
from app.models.message import LLMResponse, Message, Role, TextBlock
from app.models.tool import ToolDefinition
from app.providers.null_llm_provider import NullLLMProvider
from app.providers.openai.openai_provider import OpenAIProvider
from app.tools import RememberTool


class _FixedTextLLMProvider(LLMProvider):
    """Один и тот же текст в generate и в stream (чанками)."""

    TEXT = "Hello streaming world"

    async def generate(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> LLMResponse:
        return LLMResponse(
            message=Message(
                role=Role.ASSISTANT,
                content=[TextBlock(text=self.TEXT)],
            ),
            finish_reason="stop",
        )

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
    ) -> AsyncIterator[str]:
        # Несколько чанков — чтобы join не был тривиальным no-op.
        mid = len(self.TEXT) // 2
        yield self.TEXT[:mid]
        yield self.TEXT[mid:]


class _FakeDelta:
    def __init__(self, content: str | None) -> None:
        self.content = content


class _FakeStreamChoice:
    def __init__(self, content: str | None) -> None:
        self.delta = _FakeDelta(content)


class _FakeStreamChunk:
    def __init__(self, content: str | None) -> None:
        self.choices = [_FakeStreamChoice(content)]


async def _collect(stream: AsyncIterator[str]) -> str:
    return "".join([token async for token in stream])


def _assistant_text(response: LLMResponse) -> str:
    block = response.message.content[0]
    assert isinstance(block, TextBlock)
    return block.text


async def test_stream_joined_equals_generate_content() -> None:
    provider = _FixedTextLLMProvider()
    messages = [Message(role=Role.USER, content=[TextBlock(text="hi")])]

    generated = await provider.generate(messages)
    streamed = await _collect(provider.stream(messages))

    assert streamed == _assistant_text(generated)
    assert streamed == _FixedTextLLMProvider.TEXT


async def test_null_provider_stream_matches_generate() -> None:
    provider = NullLLMProvider()
    messages = [Message(role=Role.USER, content=[TextBlock(text="hi")])]

    generated = await provider.generate(messages)
    streamed = await _collect(provider.stream(messages))

    assert streamed == _assistant_text(generated)


async def test_openai_provider_stream_yields_deltas() -> None:
    async def fake_chat_stream(
        model: str,
        messages: list[object],
    ) -> AsyncIterator[str]:
        yield "Hel"
        yield "lo"

    client = AsyncMock()
    client.chat_stream = fake_chat_stream
    provider = OpenAIProvider(client=client, model="gpt-4o-mini")

    streamed = await _collect(
        provider.stream([Message(role=Role.USER, content=[TextBlock(text="hi")])])
    )
    assert streamed == "Hello"


async def test_openai_provider_stream_rejects_tools() -> None:
    provider = OpenAIProvider(client=AsyncMock(), model="gpt-4o-mini")
    with pytest.raises(NotImplementedError, match="tools"):
        await _collect(
            provider.stream(
                [Message(role=Role.USER, content=[TextBlock(text="hi")])],
                tools=[RememberTool().definition],
            )
        )


async def test_simple_engine_stream_turn_matches_run_turn() -> None:
    provider = _FixedTextLLMProvider()
    engine = SimpleConversationEngine(
        llm_provider=provider,
        context_builder=SimpleContextBuilder(),
    )

    run_conversation = Conversation(conversation_id="c-run")
    run_message = await engine.run_turn(
        run_conversation,
        Message(role=Role.USER, content=[TextBlock(text="hi")]),
    )

    stream_conversation = Conversation(conversation_id="c-stream")
    tokens: list[str] = []
    async for token in engine.stream_turn(
        stream_conversation,
        Message(role=Role.USER, content=[TextBlock(text="hi")]),
    ):
        tokens.append(token)

    assert "".join(tokens) == cast_text(run_message)
    assert stream_conversation.messages[-1].role == Role.ASSISTANT
    assert cast_text(stream_conversation.messages[-1]) == "".join(tokens)


def cast_text(message: Message) -> str:
    block = message.content[0]
    assert isinstance(block, TextBlock)
    return block.text
