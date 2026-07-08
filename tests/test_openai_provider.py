from unittest.mock import AsyncMock

import pytest

from app.models.message import ImageBlock, Message, Role, TextBlock
from app.providers.openai.openai_provider import OpenAIProvider


class _FakeMessage:
    def __init__(self, role: str, content: str) -> None:
        self.role = role
        self.content = content


class _FakeChoice:
    def __init__(self, role: str, content: str, finish_reason: str = "stop") -> None:
        self.message = _FakeMessage(role=role, content=content)
        self.finish_reason = finish_reason


class _FakeUsage:
    def model_dump(self) -> dict[str, int]:
        return {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}


class _FakeCompletion:
    def __init__(self, choices: list[_FakeChoice], model: str = "gpt-4o-mini", usage=None) -> None:
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
