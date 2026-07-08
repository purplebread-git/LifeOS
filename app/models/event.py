"""Событие в системе: факт + типизированный payload через Generic[T]."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from app.models.message import Message
from app.models.tool import ToolResult


class Event[T](BaseModel):
    name: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: T


MessageReceivedEvent = Event[Message]
ToolExecutedEvent = Event[ToolResult]