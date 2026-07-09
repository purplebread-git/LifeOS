from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.models.message import ImageBlock, Message, Role, TextBlock, ToolCall
from app.providers.openai.openai_provider import OpenAIProvider


class _FakeFunctionCall:
    def __init__(self, name: str, arguments: str) -> None:
        self.name = name
        self.arguments = arguments


class _FakeOpenAIToolCall:
    def __init__(self, id: str, name: str, arguments: str) -> None:
        self.id = id
        self.function = _FakeFunctionCall(name=name, arguments=arguments)


class _FakeMessage:
    def __init__(self, role: str, content: str, tool_calls: Any = None) -> None:
        self.role = role
        self.content = content
        self.tool_calls = tool_calls


class _FakeChoice:
    def __init__(
        self,
        role: str,
        content: str,
        finish_reason: str = "stop",
        tool_calls: Any = None,
    ) -> None:
        self.message = _FakeMessage(role=role, content=content, tool_calls=tool_calls)
        self.finish_reason = finish_reason


class _FakeUsage:
    def model_dump(self) -> dict[str, int]:
        return {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}


class _FakeCompletion:
    def __init__(
        self,
        choices: list[_FakeChoice],
        model: str = "gpt-4o-mini",
        usage: Any = None,
    ) -> None:
        self.choices = choices
        self.model = model
        self.usage = usage


async def test_message_with_text_block_converts_correctly() -> None:
    client = AsyncMock()
    client.chat.return_value = _FakeCompletion(
        choices=[_FakeChoice(role="assistant", content="Привет!")]
    )
    provider = OpenAIProvider(client=client, model="gpt-4o-mini")

    await provider.generate(messages=[Message(role=Role.USER, content=[TextBlock(text="Привет")])])

    sent_messages = client.chat.call_args.kwargs["messages"]
    assert sent_messages == [{"role": "user", "content": "Привет"}]


async def test_unsupported_block_raises_not_implemented() -> None:
    client = AsyncMock()
    provider = OpenAIProvider(client=client, model="gpt-4o-mini")

    with pytest.raises(NotImplementedError):
        await provider.generate(
            messages=[
                Message(
                    role=Role.USER,
                    content=[ImageBlock(uri="https://example.com/x.png")],
                )
            ]
        )


async def test_llm_response_assembled_correctly() -> None:
    client = AsyncMock()
    client.chat.return_value = _FakeCompletion(
        choices=[_FakeChoice(role="assistant", content="Ответ", finish_reason="stop")],
        usage=_FakeUsage(),
    )
    provider = OpenAIProvider(client=client, model="gpt-4o-mini")

    response = await provider.generate(
        messages=[Message(role=Role.USER, content=[TextBlock(text="Вопрос")])]
    )

    assert response.finish_reason == "stop"
    assert response.message.role == Role.ASSISTANT
    assert isinstance(response.message.content[0], TextBlock)
    assert response.message.content[0].text == "Ответ"
    assert response.metadata["model"] == "gpt-4o-mini"
    assert response.metadata["usage"]["total_tokens"] == 15


async def test_llm_response_includes_tool_calls() -> None:
    client = AsyncMock()
    client.chat.return_value = _FakeCompletion(
        choices=[
            _FakeChoice(
                role="assistant",
                content=None,
                finish_reason="tool_calls",
                tool_calls=[
                    _FakeOpenAIToolCall(
                        id="call_1",
                        name="search",
                        arguments='{"query": "hello"}',
                    )
                ],
            )
        ],
    )
    provider = OpenAIProvider(client=client, model="gpt-4o-mini")

    response = await provider.generate(
        messages=[Message(role=Role.USER, content=[TextBlock(text="Найди что-нибудь")])]
    )

    assert response.message.tool_calls == [
        ToolCall(id="call_1", tool_name="search", arguments={"query": "hello"})
    ]
    assert response.finish_reason == "tool_calls"
