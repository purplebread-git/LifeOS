from datetime import datetime, timezone
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from app.core.models import Message, ToolResult

T = TypeVar("T")


class Event(BaseModel, Generic[T]):
    """Событие в системе: факт + типизированный payload.

    Не ABC — событие это данные, а не поведение. Конкретные типы событий
    задаются не подклассами, а type-алиасами (см. ниже) — это даёт типизацию
    payload без boilerplate-класса на каждый новый тип события.
    """

    name: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: T


MessageReceivedEvent = Event[Message]
ToolExecutedEvent = Event[ToolResult]