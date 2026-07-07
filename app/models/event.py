"""Событие в системе: факт + типизированный payload через Generic[T]."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from app.models.message import Message
from app.models.tool import ToolResult

T = TypeVar("T")


class Event(BaseModel, Generic[T]):
    name: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: T


MessageReceivedEvent = Event[Message]
ToolExecutedEvent = Event[ToolResult]