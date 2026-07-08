"""Модели разговора и итогового ответа агента."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.models.message import Message


class Conversation(BaseModel):
    conversation_id: str
    messages: list[Message] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    conversation_id: str
    messages: list[Message]
    metadata: dict[str, Any] = Field(default_factory=dict)
