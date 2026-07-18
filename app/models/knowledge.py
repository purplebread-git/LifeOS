"""Доменная модель знаний.

Осознанно отдельна от app/models/memory.py: память и знания — разные
доменные сущности. Сегодня поля похожи, но их эволюция расходится (память:
user-specific, created_at, personal; знание: source, chunk, document,
citations). Дублирование честное — переиспользование MemoryEntry создало бы
ложную связанность.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class KnowledgeChunk(BaseModel):
    id: str
    content: str
    source: str
    metadata: dict[str, Any] = Field(default_factory=dict)


# Как найден кандидат: semantic — по эмбеддингу (score = cosine), substring —
# точное совпадение подстроки для чанков без эмбеддинга (fallback).
# Намеренно не импортируется из app/models/memory: строки совпадают, но
# связывать подсистемы знаний и памяти ради Literal нежелательно.
MatchType = Literal["semantic", "substring"]


class KnowledgeMatch(BaseModel):
    """Кандидат поиска знаний до ранжирования: чанк + score + тип совпадения.

    Доменная модель retrieval-слоя знаний. Живёт между provider (собирает
    кандидатов) и ranker (применяет политику). Наружу через
    KnowledgeProvider.search() не течёт — контракт остаётся list[KnowledgeChunk].
    """

    chunk: KnowledgeChunk
    score: float
    match_type: MatchType
