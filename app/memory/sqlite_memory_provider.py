"""SqliteMemoryProvider — реализация MemoryProvider поверх SQLite (async).

Память переживает перезапуск процесса. Поиск сохраняет ту же
substring-семантику, что и InMemoryMemoryProvider; семантический поиск —
отдельная итерация, интерфейс MemoryProvider при этом не меняется.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.memory_provider import MemoryProvider
from app.models.memory import MemoryEntry
from app.persistence.models import MemoryRecord


class SqliteMemoryProvider(MemoryProvider):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def add(self, entry: MemoryEntry) -> None:
        async with self._session_factory() as session:
            session.add(_to_record(entry))
            await session.commit()

    async def get(self, entry_id: str) -> MemoryEntry | None:
        async with self._session_factory() as session:
            record = await session.get(MemoryRecord, entry_id)
            return _to_entry(record) if record is not None else None

    async def update(self, entry: MemoryEntry) -> None:
        async with self._session_factory() as session:
            await session.merge(_to_record(entry))
            await session.commit()

    async def delete(self, entry_id: str) -> None:
        async with self._session_factory() as session:
            record = await session.get(MemoryRecord, entry_id)
            if record is not None:
                await session.delete(record)
                await session.commit()

    async def search(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        async with self._session_factory() as session:
            statement = (
                select(MemoryRecord)
                .where(func.lower(MemoryRecord.content).contains(query.lower()))
                .order_by(MemoryRecord.created_at)
                .limit(limit)
            )
            result = await session.execute(statement)
            return [_to_entry(record) for record in result.scalars().all()]


def _to_record(entry: MemoryEntry) -> MemoryRecord:
    return MemoryRecord(
        id=entry.id,
        content=entry.content,
        memory_metadata=entry.metadata,
        created_at=entry.created_at,
    )


def _to_entry(record: MemoryRecord) -> MemoryEntry:
    return MemoryEntry(
        id=record.id,
        content=record.content,
        metadata=record.memory_metadata,
        created_at=_as_utc(record.created_at),
    )


def _as_utc(value: datetime) -> datetime:
    """SQLite не хранит tzinfo и возвращает naive datetime. Домен и
    InMemoryMemoryProvider оперируют aware-UTC — восстанавливаем контракт,
    чтобы сравнение/ранжирование по времени не падало на naive vs aware."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
