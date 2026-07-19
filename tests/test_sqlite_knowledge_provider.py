from collections.abc import AsyncIterator
from pathlib import Path

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.knowledge.sqlite_knowledge_provider import SqliteKnowledgeProvider
from app.models.knowledge import KnowledgeChunk
from app.persistence.database import Base, create_engine


async def _make_provider(database_url: str) -> tuple[SqliteKnowledgeProvider, AsyncEngine]:
    engine = create_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return SqliteKnowledgeProvider(session_factory), engine


@pytest_asyncio.fixture
async def provider() -> AsyncIterator[SqliteKnowledgeProvider]:
    knowledge_provider, engine = await _make_provider("sqlite+aiosqlite:///:memory:")
    yield knowledge_provider
    await engine.dispose()


async def test_add_and_search(provider: SqliteKnowledgeProvider) -> None:
    await provider.add(
        KnowledgeChunk(id="1", content="Python is a programming language", source="wiki")
    )

    results = await provider.search("programming")

    assert len(results) == 1
    assert results[0].content == "Python is a programming language"
    assert results[0].source == "wiki"


async def test_metadata_roundtrips(provider: SqliteKnowledgeProvider) -> None:
    await provider.add(
        KnowledgeChunk(id="1", content="fact", source="doc", metadata={"page": 3, "lang": "en"})
    )

    results = await provider.search("fact")

    assert results[0].metadata == {"page": 3, "lang": "en"}


async def test_search_is_case_insensitive(provider: SqliteKnowledgeProvider) -> None:
    await provider.add(KnowledgeChunk(id="1", content="The Eiffel Tower is in Paris", source="doc"))

    results = await provider.search("eiffel")

    assert len(results) == 1


async def test_search_no_match_returns_empty(provider: SqliteKnowledgeProvider) -> None:
    await provider.add(KnowledgeChunk(id="1", content="unrelated", source="doc"))

    assert await provider.search("missing") == []


async def test_add_batch_stores_all(provider: SqliteKnowledgeProvider) -> None:
    await provider.add_batch(
        [
            KnowledgeChunk(id="1", content="alpha topic", source="a"),
            KnowledgeChunk(id="2", content="alpha again", source="b"),
        ]
    )

    results = await provider.search("alpha")

    assert len(results) == 2


async def test_search_respects_limit(provider: SqliteKnowledgeProvider) -> None:
    await provider.add_batch(
        [KnowledgeChunk(id=str(i), content=f"topic {i}", source="s") for i in range(6)]
    )

    results = await provider.search("topic", limit=3)

    assert len(results) == 3


async def test_add_same_id_overwrites(provider: SqliteKnowledgeProvider) -> None:
    await provider.add(KnowledgeChunk(id="1", content="old content", source="s"))
    await provider.add(KnowledgeChunk(id="1", content="new content", source="s"))

    results = await provider.search("content")

    assert len(results) == 1
    assert results[0].content == "new content"


async def test_list_sources_unique_and_sorted(provider: SqliteKnowledgeProvider) -> None:
    await provider.add_batch(
        [
            KnowledgeChunk(id="1", content="a", source="zeta"),
            KnowledgeChunk(id="2", content="b", source="alpha"),
            KnowledgeChunk(id="3", content="c", source="alpha"),
        ]
    )

    assert await provider.list_sources() == ["alpha", "zeta"]


async def test_delete_source_removes_only_its_chunks(provider: SqliteKnowledgeProvider) -> None:
    await provider.add_batch(
        [
            KnowledgeChunk(id="1", content="alpha one", source="a"),
            KnowledgeChunk(id="2", content="alpha two", source="a"),
            KnowledgeChunk(id="3", content="alpha three", source="b"),
        ]
    )

    deleted = await provider.delete_source("a")

    assert deleted == 2
    assert await provider.list_sources() == ["b"]
    assert len(await provider.search("alpha")) == 1


async def test_delete_source_is_idempotent(provider: SqliteKnowledgeProvider) -> None:
    await provider.add(KnowledgeChunk(id="1", content="x", source="a"))

    assert await provider.delete_source("missing") == 0
    assert await provider.delete_source("a") == 1
    assert await provider.delete_source("a") == 0


async def test_knowledge_survives_engine_restart(tmp_path: Path) -> None:
    # Acceptance-тест PR: add → restart → search → knowledge survives.
    database_url = f"sqlite+aiosqlite:///{tmp_path}/knowledge.db"

    first_provider, first_engine = await _make_provider(database_url)
    await first_provider.add(
        KnowledgeChunk(id="1", content="LifeOS is a modular platform", source="handbook")
    )
    await first_engine.dispose()

    second_provider, second_engine = await _make_provider(database_url)
    results = await second_provider.search("modular")
    await second_engine.dispose()

    assert len(results) == 1
    assert results[0].content == "LifeOS is a modular platform"
    assert results[0].source == "handbook"
