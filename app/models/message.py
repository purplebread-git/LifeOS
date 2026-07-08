"""Модели сообщений и мультимодального контента."""
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
    uri: str
    mime_type: str | None = None


class AudioBlock(BaseModel):
    type: Literal["audio"] = "audio"
    uri: str
    mime_type: str | None = None


class FileBlock(BaseModel):
    type: Literal["file"] = "file"
    uri: str
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