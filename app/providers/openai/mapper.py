"""Конвертация между моделями ядра (Message, ToolDefinition, LLMResponse)
и форматом OpenAI Chat Completions API.

Выделено в отдельный модуль намеренно: когда появятся AnthropicProvider и
GeminiProvider, у каждого будет свой mapper.py с той же сигнатурой ролей
и той же структурой — а сам *Provider останется тонким оркестратором,
который просто вызывает mapper + client.
"""

from __future__ import annotations

import json
from typing import Any

from app.models.message import LLMResponse, Message, Role, TextBlock, ToolCall
from app.models.tool import ToolDefinition
from app.providers.openai.types import OpenAIFunctionDef, OpenAIMessage, OpenAIToolDef

_ROLE_TO_OPENAI: dict[Role, str] = {
    Role.SYSTEM: "system",
    Role.USER: "user",
    Role.ASSISTANT: "assistant",
    Role.TOOL: "tool",
}

_OPENAI_TO_ROLE: dict[str, Role] = {value: key for key, value in _ROLE_TO_OPENAI.items()}


def message_to_openai(message: Message) -> OpenAIMessage:
    openai_message: OpenAIMessage = {
        "role": _ROLE_TO_OPENAI[message.role],
        "content": _content_blocks_to_text(message),
    }

    if message.tool_calls:
        openai_message["tool_calls"] = [
            {
                "id": tool_call.id,
                "type": "function",
                "function": {
                    "name": tool_call.tool_name,
                    "arguments": json.dumps(tool_call.arguments),
                },
            }
            for tool_call in message.tool_calls
        ]

    if message.tool_call_id is not None:
        openai_message["tool_call_id"] = message.tool_call_id

    return openai_message


def _content_blocks_to_text(message: Message) -> str:
    text_parts: list[str] = []

    for block in message.content:
        if isinstance(block, TextBlock):
            text_parts.append(block.text)
        else:
            raise NotImplementedError(
                f"Блок контента типа '{block.type}' пока не поддерживается "
                f"OpenAIProvider — в этой итерации реализован только TextBlock."
            )

    return "\n".join(text_parts)


def tool_definition_to_openai(tool_definition: ToolDefinition) -> OpenAIToolDef:
    function_def: OpenAIFunctionDef = {
        "name": tool_definition.name,
        "description": tool_definition.description,
        "parameters": tool_definition.input_schema,
    }

    return {
        "type": "function",
        "function": function_def,
    }


def completion_to_llm_response(completion: Any) -> LLMResponse:
    choice = completion.choices[0]

    role = _OPENAI_TO_ROLE.get(choice.message.role, Role.ASSISTANT)
    content = choice.message.content or ""

    tool_calls = _openai_tool_calls_to_tool_calls(choice.message)

    message = Message(
        role=role,
        content=[TextBlock(text=content)],
        tool_calls=tool_calls,
    )

    usage = completion.usage.model_dump() if completion.usage else {}

    return LLMResponse(
        message=message,
        finish_reason=choice.finish_reason or "stop",
        metadata={
            "model": completion.model,
            "usage": usage,
        },
    )


def _openai_tool_calls_to_tool_calls(openai_message: Any) -> list[ToolCall]:
    """Обратная конвертация OpenAI tool_calls -> ToolCall.

    getattr используется намеренно: старые/фейковые объекты сообщений в
    тестах не всегда несут атрибут tool_calls, а реальный SDK-объект
    отдаёт None, если tool calls не было — оба случая не должны падать.
    """
    raw_tool_calls = getattr(openai_message, "tool_calls", None)

    if not raw_tool_calls:
        return []

    return [
        ToolCall(
            id=raw_tool_call.id,
            tool_name=raw_tool_call.function.name,
            arguments=json.loads(raw_tool_call.function.arguments),
        )
        for raw_tool_call in raw_tool_calls
    ]
