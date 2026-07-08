"""Общие data-контракты между абстракциями ядра.

Это не бизнес-логика — это форма данных, которой обмениваются интерфейсы.
"""
from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, field_validator


class Role(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class TextBlock(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ImageBlock(BaseModel):
    type: Literal["image"] = "image"
    source: str  # URL или base64 — конкретный формат конвертирует Provider
    mime_type: str | None = None


class AudioBlock(BaseModel):
    type: Literal["audio"] = "audio"
    source: str
    mime_type: str | None = None


class FileBlock(BaseModel):
    type: Literal["file"] = "file"
    source: str
    mime_type: str | None = None
    filename: str | None = None


ContentBlock = Annotated[
    TextBlock | ImageBlock | AudioBlock | FileBlock,
    Field(discriminator="type"),
]


class ToolCall(BaseModel):
    id: str
    tool_name: str
    arguments: dict[str, Any]


class Message(BaseModel):
    """Сообщение в диалоге.

    content — список блоков контента (мультимодальность). Для удобства можно
    передать обычную строку — она автоматически обернётся в [TextBlock(...)].
    """

    role: Role
    content: list[ContentBlock]
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_call_id: str | None = None

    @field_validator("content", mode="before")
    @classmethod
    def _wrap_plain_text(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [TextBlock(text=value)]
        return value


class LLMResponse(BaseModel):
    message: Message
    finish_reason: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    tool_call_id: str
    content: str
    is_error: bool = False


class ToolDefinition(BaseModel):
    """Описание инструмента для LLM.

    input_schema — JSON Schema (json-schema.org), открытый стандарт,
    независимо используемый OpenAI, Claude, Gemini и протоколом MCP.
    Это не заимствование терминологии у конкретного вендора.
    """

    name: str
    description: str
    input_schema: dict[str, Any]


class MemoryEntry(BaseModel):
    id: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Conversation(BaseModel):
    conversation_id: str
    messages: list[Message] = Field(default_factory=list)


class AgentResponse(BaseModel):
    """Итоговый ответ агента на один запрос пользователя.

    messages — список: агент может вернуть несколько сообщений за один ход.
    metadata — точка роста под usage/latency/model/finish_reason/streaming,
    чтобы не раздувать саму модель новыми top-level полями в будущем.
    """

    conversation_id: str
    messages: list[Message]
    metadata: dict[str, Any] = Field(default_factory=dict)