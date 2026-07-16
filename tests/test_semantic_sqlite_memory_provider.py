from collections.abc import AsyncIterator
from pathlib import Path

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.core.embedding_provider import EmbeddingProvider
from app.core.exceptions import EmbeddingError
from app.memory.semantic_sqlite_memory_provider import SemanticSqliteMemoryProvider
from app.memory.threshold_memory_ranker import ThresholdMemoryRanker
from app.models.memory import MemoryEntry
from app.persistence.database import Base, create_engine

# Концепт-эмбеддер: слова разных формулировок мапятся на общие оси смысла.
# Позволяет проверить semantic retrieval без реальных вызовов OpenAI и без
# совпадения слов между запросом и памятью.
_CONCEPTS: dict[str, set[str]] = {
    "work": {"work", "job", "apple", "store", "employed", "career"},
    "location": {"live", "lives", "city", "novgorod", "where"},
    "music": {"music", "rock", "guitar", "love"},
    "height": {"height", "tall", "cm"},
}


def _concept_vector(text: str) -> list[float]:
    tokens = {token.strip("?.,!").lower() for token in text.split()}
    return [float(len(tokens & words)) for words in _CONCEPTS.values()]


class FakeEmbeddingProvider(EmbeddingProvider):
    def __init__(self) -> None:
        self.fail = False

    async def embed(self, text: str) -> list[float]:
        if self.fail:
            raise EmbeddingError("simulated embedding failure")
        return _concept_vector(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self.fail:
            raise EmbeddingError("simulated embedding failure")
        return [_concept_vector(text) for text in texts]


async def _make_provider(
    database_url: str,
    embedder: EmbeddingProvider,
    min_score: float = 0.25,
) -> tuple[SemanticSqliteMemoryProvider, AsyncEngine]:
    engine = create_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    ranker = ThresholdMemoryRanker(min_score=min_score)
    return SemanticSqliteMemoryProvider(session_factory, embedder, ranker), engine


@pytest_asyncio.fixture
async def provider() -> AsyncIterator[SemanticSqliteMemoryProvider]:
    memory_provider, engine = await _make_provider(
        "sqlite+aiosqlite:///:memory:",
        FakeEmbeddingProvider(),
    )
    yield memory_provider
    await engine.dispose()


async def test_add_and_get(provider: SemanticSqliteMemoryProvider) -> None:
    await provider.add(MemoryEntry(id="1", content="I work at an Apple store"))

    entry = await provider.get("1")

    assert entry is not None
    assert entry.content == "I work at an Apple store"


async def test_semantic_search_finds_memory_without_shared_words(
    provider: SemanticSqliteMemoryProvider,
) -> None:
    await provider.add(MemoryEntry(id="1", content="I work at an Apple store"))
    await provider.add(MemoryEntry(id="2", content="I love rock music"))
    await provider.add(MemoryEntry(id="3", content="My height is 171 cm"))

    # Запрос не разделяет НИ ОДНОГО слова с целевым воспоминанием.
    results = await provider.search("What is my job?")

    assert results[0].content == "I work at an Apple store"


async def test_threshold_filters_unrelated_memories(
    provider: SemanticSqliteMemoryProvider,
) -> None:
    # Классический шум: вопрос не про пользователя, но раньше top-k всё равно
    # тащил в контекст нерелевантные воспоминания.
    await provider.add(MemoryEntry(id="1", content="I love rock music"))
    await provider.add(MemoryEntry(id="2", content="My height is 171 cm"))

    results = await provider.search("What is my job?")

    assert results == []


async def test_semantic_ranks_by_similarity(
    provider: SemanticSqliteMemoryProvider,
) -> None:
    await provider.add(MemoryEntry(id="1", content="I love rock music"))
    await provider.add(MemoryEntry(id="2", content="My height is 171 cm"))

    results = await provider.search("Tell me about guitar and rock")

    assert results[0].content == "I love rock music"


async def test_search_respects_limit(provider: SemanticSqliteMemoryProvider) -> None:
    for index in range(6):
        await provider.add(MemoryEntry(id=str(index), content=f"I love music {index}"))

    results = await provider.search("music", limit=3)

    assert len(results) == 3


async def test_embedding_failure_on_add_still_saves() -> None:
    embedder = FakeEmbeddingProvider()
    embedder.fail = True
    memory_provider, engine = await _make_provider("sqlite+aiosqlite:///:memory:", embedder)

    await memory_provider.add(MemoryEntry(id="1", content="I love rock music"))
    entry = await memory_provider.get("1")

    await engine.dispose()

    assert entry is not None
    assert entry.content == "I love rock music"


async def test_search_falls_back_to_substring_when_query_embed_fails() -> None:
    embedder = FakeEmbeddingProvider()
    memory_provider, engine = await _make_provider("sqlite+aiosqlite:///:memory:", embedder)

    await memory_provider.add(MemoryEntry(id="1", content="I love rock music"))

    embedder.fail = True
    results = await memory_provider.search("rock")

    await engine.dispose()

    assert len(results) == 1
    assert results[0].content == "I love rock music"


async def test_substring_fallback_for_null_embedding_entries() -> None:
    embedder = FakeEmbeddingProvider()
    memory_provider, engine = await _make_provider("sqlite+aiosqlite:///:memory:", embedder)

    # Запись сохранена во время сбоя embeddings → embedding IS NULL.
    embedder.fail = True
    await memory_provider.add(MemoryEntry(id="null", content="I love rock music"))

    # Другая запись сохранена нормально → с эмбеддингом.
    embedder.fail = False
    await memory_provider.add(MemoryEntry(id="ok", content="I work at an Apple store"))

    # Запрос эмбеддится успешно; NULL-запись находится substring-добором.
    results = await memory_provider.search("rock")

    await engine.dispose()

    contents = [entry.content for entry in results]
    assert "I love rock music" in contents


async def test_update_reembeds(provider: SemanticSqliteMemoryProvider) -> None:
    await provider.add(MemoryEntry(id="1", content="I love rock music"))

    await provider.update(MemoryEntry(id="1", content="I work at an Apple store"))

    results = await provider.search("What is my job?")
    assert results[0].content == "I work at an Apple store"


async def test_delete_removes_entry(provider: SemanticSqliteMemoryProvider) -> None:
    await provider.add(MemoryEntry(id="1", content="I love rock music"))

    await provider.delete("1")

    assert await provider.get("1") is None


async def test_memory_survives_engine_restart(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path}/semantic.db"

    first, first_engine = await _make_provider(database_url, FakeEmbeddingProvider())
    await first.add(MemoryEntry(id="1", content="I work at an Apple store"))
    await first_engine.dispose()

    second, second_engine = await _make_provider(database_url, FakeEmbeddingProvider())
    results = await second.search("What is my job?")
    await second_engine.dispose()

    assert results[0].content == "I work at an Apple store"
