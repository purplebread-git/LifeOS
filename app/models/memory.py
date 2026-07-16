from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(UTC)


class MemoryEntry(BaseModel):
    id: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utcnow)


# Как записан кандидат в результатах поиска: semantic — по эмбеддингу
# (score = cosine), substring — точное совпадение подстроки для записей без
# эмбеддинга (fallback). Ranker может применять разную политику к каждому типу.
MatchType = Literal["semantic", "substring"]


class MemoryMatch(BaseModel):
    """Кандидат поиска до ранжирования: запись + её score + тип совпадения.

    Доменная модель retrieval-слоя. Живёт между provider (собирает кандидатов)
    и ranker (применяет политику). Наружу через MemoryProvider.search() не течёт
    — контракт остаётся list[MemoryEntry]."""

    entry: MemoryEntry
    score: float
    match_type: MatchType
