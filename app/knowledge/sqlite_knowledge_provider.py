"""SqliteKnowledgeProvider — реализация KnowledgeProvider поверх SQLite (async).

Знания переживают перезапуск процесса. Поиск сохраняет ту же
substring-семантику, что и InMemoryKnowledgeProvider; semantic-поиск и
ranking — отдельные итерации, интерфейс KnowledgeProvider при этом не меняется.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.knowledge_provider import KnowledgeProvider
from app.models.knowledge import KnowledgeChunk
from app.persistence.models import KnowledgeRecord


class SqliteKnowledgeProvider(KnowledgeProvider):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def add(self, chunk: KnowledgeChunk) -> None:
        async with self._session_factory() as session:
            await session.merge(_to_record(chunk))
            await session.commit()

    async def add_batch(self, chunks: list[KnowledgeChunk]) -> None:
        async with self._session_factory() as session:
            for chunk in chunks:
                await session.merge(_to_record(chunk))
            await session.commit()

    async def search(self, query: str, limit: int = 5) -> list[KnowledgeChunk]:
        async with self._session_factory() as session:
            statement = (
                select(KnowledgeRecord)
                .where(func.lower(KnowledgeRecord.content).contains(query.lower()))
                .order_by(KnowledgeRecord.id)
                .limit(limit)
            )
            result = await session.execute(statement)
            return [_to_chunk(record) for record in result.scalars().all()]


def _to_record(chunk: KnowledgeChunk) -> KnowledgeRecord:
    return KnowledgeRecord(
        id=chunk.id,
        content=chunk.content,
        source=chunk.source,
        knowledge_metadata=chunk.metadata,
    )


def _to_chunk(record: KnowledgeRecord) -> KnowledgeChunk:
    return KnowledgeChunk(
        id=record.id,
        content=record.content,
        source=record.source,
        metadata=record.knowledge_metadata,
    )
