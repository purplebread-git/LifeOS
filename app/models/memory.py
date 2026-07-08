from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MemoryEntry(BaseModel):
    id: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
