from types import SimpleNamespace

import pytest

from app.models.message import ImageBlock, Message, Role, TextBlock, ToolCall
from app.models.tool import ToolDefinition
from app.providers.openai import mapper


def test_message_to_openai_converts_text_block() -> None:
    message = Message(role=Role.USER, content=[TextBlock(text="Привет")])

    result = mapper.message_to_openai(message)

    assert result == {"role": "user", "content": "Привет"}


def test_message_to_openai_raises_on_unsupported_block() -> None:
    message = Message(role=Role.USER, content=[ImageBlock(uri="https://example.com/x.png")])

    with pytest.raises(NotImplementedError):
        mapper.message_to_openai(message)


def test_tool_definition_to_openai_matches_function_calling_schema() -> None:
    tool_definition = ToolDefinition(
        name="search",
        description="Search the web",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
    )

    result = mapper.tool_definition_to_openai(tool_definition)

    assert result == {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Search the web",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
        },
    }


def test_message_to_openai_converts_tool_calls() -> None:
    message = Message(
        role=Role.ASSISTANT,
        content=[TextBlock(text="")],
        tool_calls=[
            ToolCall(
                id="call_1",
                tool_name="search",
                arguments={"query": "hello"},
            )
        ],
    )

    result = mapper.message_to_openai(message)

    assert result["tool_calls"] == [
        {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "search",
                "arguments": '{"query": "hello"}',
            },
        }
    ]


def test_completion_to_llm_response_converts_tool_calls() -> None:
    completion = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    role="assistant",
                    content=None,
                    tool_calls=[
                        SimpleNamespace(
                            id="call_1",
                            function=SimpleNamespace(
                                name="search",
                                arguments='{"query": "hello"}',
                            ),
                        )
                    ],
                ),
                finish_reason="tool_calls",
            )
        ],
        model="gpt-4o-mini",
        usage=None,
    )

    result = mapper.completion_to_llm_response(completion)

    assert result.message.tool_calls == [
        ToolCall(id="call_1", tool_name="search", arguments={"query": "hello"})
    ]
    assert result.finish_reason == "tool_calls"


def test_completion_to_llm_response_without_tool_calls_returns_empty_list() -> None:
    completion = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(role="assistant", content="Привет!"),
                finish_reason="stop",
            )
        ],
        model="gpt-4o-mini",
        usage=None,
    )

    result = mapper.completion_to_llm_response(completion)

    assert result.message.tool_calls == []
