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

Similarity score считается внутри (MemoryMatch), а политику отбора —
порог, сортировку, лимит — применяет инъектируемый MemoryRanker. Контракт
MemoryProvider.search() не меняется: наружу отдаётся list[MemoryEntry], score
и тип совпадения не текут через систему.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.embedding_provider import EmbeddingProvider
from app.core.exceptions import EmbeddingError
from app.core.memory_provider import MemoryProvider
from app.core.memory_ranker import MemoryRanker
from app.memory.similarity import cosine_similarity
from app.models.memory import MemoryEntry, MemoryMatch
from app.persistence.models import MemoryRecord

# Score-заглушка для substring-кандидатов (без эмбеддинга): семантический порог
# к ним не применяется, поэтому конкретное значение на ранжирование не влияет.
_SUBSTRING_FALLBACK_SCORE = 0.0


class SemanticSqliteMemoryProvider(MemoryProvider):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        embedding_provider: EmbeddingProvider,
        ranker: MemoryRanker,
    ) -> None:
        self._session_factory = session_factory
        self._embedding_provider = embedding_provider
        self._ranker = ranker

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
        matches = await self._collect_matches(query)
        return self._ranker.rank(matches, limit)

    async def _collect_matches(self, query: str) -> list[MemoryMatch]:
        """Собирает кандидатов со score и типом совпадения — без политики отбора.

        Порог/сортировку/лимит применяет ranker; провайдер лишь считает score.
        """
        query_vec = await self._safe_embed(query)

        async with self._session_factory() as session:
            records = list((await session.execute(select(MemoryRecord))).scalars().all())

        if query_vec is None:
            # Полная деградация: эмбеддинг запроса недоступен → substring по всем.
            return [
                MemoryMatch(
                    entry=_to_entry(record),
                    score=_SUBSTRING_FALLBACK_SCORE,
                    match_type="substring",
                )
                for record in records
                if query.lower() in record.content.lower()
            ]

        matches: list[MemoryMatch] = []
        for record in records:
            if record.embedding:
                score = cosine_similarity(query_vec, record.embedding)
                matches.append(
                    MemoryMatch(entry=_to_entry(record), score=score, match_type="semantic")
                )
            elif query.lower() in record.content.lower():
                matches.append(
                    MemoryMatch(
                        entry=_to_entry(record),
                        score=_SUBSTRING_FALLBACK_SCORE,
                        match_type="substring",
                    )
                )
        return matches

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
