from collections.abc import AsyncIterator
from datetime import timedelta
from pathlib import Path

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.memory.sqlite_memory_provider import SqliteMemoryProvider
from app.models.memory import MemoryEntry
from app.persistence.database import Base, create_engine


async def _make_provider(database_url: str) -> tuple[SqliteMemoryProvider, AsyncEngine]:
    engine = create_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return SqliteMemoryProvider(session_factory), engine


@pytest_asyncio.fixture
async def provider() -> AsyncIterator[SqliteMemoryProvider]:
    memory_provider, engine = await _make_provider("sqlite+aiosqlite:///:memory:")
    yield memory_provider
    await engine.dispose()


async def test_add_and_get(provider: SqliteMemoryProvider) -> None:
    await provider.add(MemoryEntry(id="1", content="I love rock music"))

    entry = await provider.get("1")

    assert entry is not None
    assert entry.content == "I love rock music"


async def test_get_missing_returns_none(provider: SqliteMemoryProvider) -> None:
    assert await provider.get("nope") is None


async def test_created_at_roundtrips_as_utc_aware(provider: SqliteMemoryProvider) -> None:
    await provider.add(MemoryEntry(id="1", content="x"))

    entry = await provider.get("1")

    assert entry is not None
    assert entry.created_at.tzinfo is not None
    assert entry.created_at.utcoffset() == timedelta(0)


async def test_search_substring(provider: SqliteMemoryProvider) -> None:
    await provider.add(MemoryEntry(id="1", content="User height is 171 cm"))
    await provider.add(MemoryEntry(id="2", content="User lives in Nizhny Novgorod"))

    results = await provider.search("height")

    assert len(results) == 1
    assert results[0].id == "1"


async def test_search_is_case_insensitive(provider: SqliteMemoryProvider) -> None:
    await provider.add(MemoryEntry(id="1", content="I love ROCK music"))

    results = await provider.search("rock")

    assert len(results) == 1


async def test_search_respects_limit(provider: SqliteMemoryProvider) -> None:
    for index in range(10):
        await provider.add(MemoryEntry(id=str(index), content=f"topic alpha {index}"))

    results = await provider.search("alpha", limit=3)

    assert len(results) == 3


async def test_update_overwrites_content(provider: SqliteMemoryProvider) -> None:
    await provider.add(MemoryEntry(id="1", content="old"))

    await provider.update(MemoryEntry(id="1", content="new"))

    entry = await provider.get("1")
    assert entry is not None
    assert entry.content == "new"


async def test_delete_removes_entry(provider: SqliteMemoryProvider) -> None:
    await provider.add(MemoryEntry(id="1", content="temporary"))

    await provider.delete("1")

    assert await provider.get("1") is None


async def test_memory_survives_engine_restart(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path}/memory.db"

    first_provider, first_engine = await _make_provider(database_url)
    await first_provider.add(MemoryEntry(id="1", content="I love rock music"))
    await first_engine.dispose()

    second_provider, second_engine = await _make_provider(database_url)
    results = await second_provider.search("rock")
    await second_engine.dispose()

    assert len(results) == 1
    assert results[0].content == "I love rock music"
