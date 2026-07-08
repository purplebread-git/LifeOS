"""Конвертация между моделями ядра (Message, ToolDefinition, LLMResponse)
и форматом OpenAI Chat Completions API.

Выделено в отдельный модуль намеренно: когда появятся AnthropicProvider и
GeminiProvider, у каждого будет свой mapper.py с той же сигнатурой ролей
и той же структурой — а сам *Provider останется тонким оркестратором,
который просто вызывает mapper + client.
"""

from __future__ import annotations

from typing import Any

from app.models.message import LLMResponse, Message, Role, TextBlock
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
    # TODO(iteration-6): message.tool_calls конвертация в формат OpenAI
    # tool_calls появится вместе с ToolManager. Пока список почти всегда
    # пуст (ToolManager ещё не существует) — намеренно НЕ бросаем исключение
    # здесь, чтобы случайно не уронить агента, если поле окажется заполнено.

    openai_message: OpenAIMessage = {
        "role": _ROLE_TO_OPENAI[message.role],
        "content": _content_blocks_to_text(message),
    }

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
    # Формат уже соответствует ожидаемой OpenAI function-calling schema —
    # это делает провайдер готовым к ToolManager без изменений в мэппере.
    function_def: OpenAIFunctionDef = {
        "name": tool_definition.name,
        "description": tool_definition.description,
        "parameters": tool_definition.input_schema,
    }
    return {"type": "function", "function": function_def}


def completion_to_llm_response(completion: Any) -> LLMResponse:
    choice = completion.choices[0]

    # TODO(iteration-6): choice.message.tool_calls обрабатываются здесь,
    # когда появится ToolManager. Пока намеренно игнорируем это поле, а не
    # бросаем исключение — если OpenAI вернёт tool_calls раньше, чем мы
    # готовы их обработать, агент не должен падать.

    role = _OPENAI_TO_ROLE.get(choice.message.role, Role.ASSISTANT)
    content = choice.message.content or ""

    message = Message(role=role, content=[TextBlock(text=content)])

    usage = completion.usage.model_dump() if completion.usage else {}

    return LLMResponse(
        message=message,
        finish_reason=choice.finish_reason or "stop",
        metadata={"model": completion.model, "usage": usage},
    )
