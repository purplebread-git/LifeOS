"""SemanticSqliteMemoryProvider — persistent memory (SQLite) с semantic-поиском.

Всё ещё persistent memory provider: контент, метаданные и created_at
сохраняются всегда. Дополнительно хранит эмбеддинг записи и ищет по
косинусной близости.

Устойчивость к сбоям embeddings — обязательное требование:
  * add/update: запись сохраняется даже если эмбеддинг получить не удалось
    (embedding = NULL);
  * search: если эмбеддинг запроса получить не удалось — полный откат к
    substring; иначе semantic по записям с эмбеддингом + substring-добор для
    записей с embedding IS NULL.

Similarity score считается уже сейчас (внутренне), но контракт
MemoryProvider.search() не меняется — наружу отдаётся list[MemoryEntry].
Это делает будущий Memory Ranking (порог/веса) дешёвым.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.embedding_provider import EmbeddingProvider
from app.core.exceptions import EmbeddingError
from app.core.memory_provider import MemoryProvider
from app.memory.similarity import cosine_similarity
from app.models.memory import MemoryEntry
from app.persistence.models import MemoryRecord

ScoredMemory = tuple[MemoryEntry, float]

# Sentinel-score для записей, найденных substring-добором (без эмбеддинга):
# ранжируются после настоящих semantic-хитов.
_SUBSTRING_FALLBACK_SCORE = 0.0


class SemanticSqliteMemoryProvider(MemoryProvider):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self._session_factory = session_factory
        self._embedding_provider = embedding_provider

    async def add(self, entry: MemoryEntry) -> None:
        embedding = await self._safe_embed(entry.content)
        async with self._session_factory() as session:
            session.add(_to_record(entry, embedding))
            await session.commit()

    async def get(self, entry_id: str) -> MemoryEntry | None:
        async with self._session_factory() as session:
            record = await session.get(MemoryRecord, entry_id)
            return _to_entry(record) if record is not None else None

    async def update(self, entry: MemoryEntry) -> None:
        embedding = await self._safe_embed(entry.content)
        async with self._session_factory() as session:
            await session.merge(_to_record(entry, embedding))
            await session.commit()

    async def delete(self, entry_id: str) -> None:
        async with self._session_factory() as session:
            record = await session.get(MemoryRecord, entry_id)
            if record is not None:
                await session.delete(record)
                await session.commit()

    async def search(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        scored = await self._search_scored(query, limit)
        return [entry for entry, _ in scored]

    async def _search_scored(self, query: str, limit: int) -> list[ScoredMemory]:
        query_vec = await self._safe_embed(query)

        async with self._session_factory() as session:
            records = list((await session.execute(select(MemoryRecord))).scalars().all())

        if query_vec is None:
            # Полная деградация: эмбеддинг запроса недоступен → substring по всем.
            matches = [
                (_to_entry(record), _SUBSTRING_FALLBACK_SCORE)
                for record in records
                if query.lower() in record.content.lower()
            ]
            return matches[:limit]

        semantic: list[ScoredMemory] = []
        substring_fallback: list[ScoredMemory] = []
        for record in records:
            if record.embedding:
                score = cosine_similarity(query_vec, record.embedding)
                semantic.append((_to_entry(record), score))
            elif query.lower() in record.content.lower():
                substring_fallback.append((_to_entry(record), _SUBSTRING_FALLBACK_SCORE))

        semantic.sort(key=lambda pair: pair[1], reverse=True)
        return (semantic + substring_fallback)[:limit]

    async def _safe_embed(self, text: str) -> list[float] | None:
        try:
            return await self._embedding_provider.embed(text)
        except EmbeddingError:
            return None


def _to_record(entry: MemoryEntry, embedding: list[float] | None) -> MemoryRecord:
    return MemoryRecord(
        id=entry.id,
        content=entry.content,
        memory_metadata=entry.metadata,
        created_at=entry.created_at,
        embedding=embedding,
    )


def _to_entry(record: MemoryRecord) -> MemoryEntry:
    return MemoryEntry(
        id=record.id,
        content=record.content,
        metadata=record.memory_metadata,
        created_at=_as_utc(record.created_at),
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
