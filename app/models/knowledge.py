"""Доменная модель знаний.

Осознанно отдельна от app/models/memory.py: память и знания — разные
доменные сущности. Сегодня поля похожи, но их эволюция расходится (память:
user-specific, created_at, personal; знание: source, chunk, document,
citations). Дублирование честное — переиспользование MemoryEntry создало бы
ложную связанность.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class KnowledgeChunk(BaseModel):
    id: str
    content: str
    source: str
    metadata: dict[str, Any] = Field(default_factory=dict)
