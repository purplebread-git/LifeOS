from collections.abc import AsyncIterator
from pathlib import Path

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.core.embedding_provider import EmbeddingProvider
from app.core.exceptions import EmbeddingError
from app.knowledge.semantic_sqlite_knowledge_provider import SemanticSqliteKnowledgeProvider
from app.knowledge.threshold_knowledge_ranker import ThresholdKnowledgeRanker
from app.models.knowledge import KnowledgeChunk
from app.persistence.database import Base, create_engine

# Концепт-эмбеддер: разные формулировки мапятся на общие оси смысла. Позволяет
# проверить semantic retrieval без реальных вызовов OpenAI и без совпадения
# слов между запросом и знанием.
_CONCEPTS: dict[str, set[str]] = {
    "language": {"python", "programming", "language", "code", "coding"},
    "geography": {"paris", "france", "city", "capital", "where", "located"},
    "space": {"moon", "planet", "orbit", "space", "astronomy"},
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
) -> tuple[SemanticSqliteKnowledgeProvider, AsyncEngine]:
    engine = create_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    ranker = ThresholdKnowledgeRanker(min_score=min_score)
    return SemanticSqliteKnowledgeProvider(session_factory, embedder, ranker), engine


@pytest_asyncio.fixture
async def provider() -> AsyncIterator[SemanticSqliteKnowledgeProvider]:
    knowledge_provider, engine = await _make_provider(
        "sqlite+aiosqlite:///:memory:",
        FakeEmbeddingProvider(),
    )
    yield knowledge_provider
    await engine.dispose()


async def test_add_and_search(provider: SemanticSqliteKnowledgeProvider) -> None:
    await provider.add(
        KnowledgeChunk(id="1", content="Python is a programming language", source="wiki")
    )

    results = await provider.search("Tell me about coding")

    assert results[0].content == "Python is a programming language"
    assert results[0].source == "wiki"


async def test_semantic_search_finds_chunk_without_shared_words(
    provider: SemanticSqliteKnowledgeProvider,
) -> None:
    await provider.add(KnowledgeChunk(id="1", content="Paris is the capital", source="geo"))
    await provider.add(KnowledgeChunk(id="2", content="Python is a language", source="wiki"))
    await provider.add(KnowledgeChunk(id="3", content="The moon orbits Earth", source="space"))

    # Запрос не разделяет НИ ОДНОГО слова с целевым чанком.
    results = await provider.search("Where is France located?")

    assert results[0].content == "Paris is the capital"


async def test_threshold_filters_unrelated_chunks(
    provider: SemanticSqliteKnowledgeProvider,
) -> None:
    # Шум: вопрос про географию, но раньше top-k тащил и нерелевантные чанки.
    await provider.add(KnowledgeChunk(id="1", content="Python is a language", source="wiki"))
    await provider.add(KnowledgeChunk(id="2", content="The moon orbits Earth", source="space"))

    results = await provider.search("Where is France located?")

    assert results == []


async def test_semantic_ranks_by_similarity(
    provider: SemanticSqliteKnowledgeProvider,
) -> None:
    await provider.add(KnowledgeChunk(id="1", content="Python programming language", source="a"))
    await provider.add(KnowledgeChunk(id="2", content="Paris is a city", source="b"))

    results = await provider.search("coding and code")

    assert results[0].content == "Python programming language"


async def test_search_respects_limit(provider: SemanticSqliteKnowledgeProvider) -> None:
    await provider.add_batch(
        [KnowledgeChunk(id=str(i), content=f"programming code {i}", source="s") for i in range(6)]
    )

    results = await provider.search("coding", limit=3)

    assert len(results) == 3


async def test_embedding_failure_on_add_still_saves() -> None:
    embedder = FakeEmbeddingProvider()
    embedder.fail = True
    provider, engine = await _make_provider("sqlite+aiosqlite:///:memory:", embedder)

    await provider.add(KnowledgeChunk(id="1", content="Python is a language", source="wiki"))

    # embedding запроса тоже падает → полный откат к substring; чанк сохранён.
    results = await provider.search("Python")
    await engine.dispose()

    assert len(results) == 1
    assert results[0].content == "Python is a language"


async def test_search_falls_back_to_substring_when_query_embed_fails() -> None:
    embedder = FakeEmbeddingProvider()
    provider, engine = await _make_provider("sqlite+aiosqlite:///:memory:", embedder)

    await provider.add(KnowledgeChunk(id="1", content="Python is a language", source="wiki"))

    embedder.fail = True
    results = await provider.search("Python")
    await engine.dispose()

    assert len(results) == 1
    assert results[0].content == "Python is a language"


async def test_substring_fallback_for_null_embedding_chunks() -> None:
    embedder = FakeEmbeddingProvider()
    provider, engine = await _make_provider("sqlite+aiosqlite:///:memory:", embedder)

    # Чанк сохранён во время сбоя embeddings → embedding IS NULL.
    embedder.fail = True
    await provider.add(KnowledgeChunk(id="null", content="Python is a language", source="wiki"))

    # Другой чанк сохранён нормально → с эмбеддингом.
    embedder.fail = False
    await provider.add(KnowledgeChunk(id="ok", content="Paris is the capital", source="geo"))

    # Запрос эмбеддится успешно; NULL-чанк находится substring-добором.
    results = await provider.search("Python")
    await engine.dispose()

    contents = [chunk.content for chunk in results]
    assert "Python is a language" in contents


async def test_knowledge_survives_engine_restart(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path}/semantic_knowledge.db"

    first, first_engine = await _make_provider(database_url, FakeEmbeddingProvider())
    await first.add(KnowledgeChunk(id="1", content="Python is a language", source="wiki"))
    await first_engine.dispose()

    second, second_engine = await _make_provider(database_url, FakeEmbeddingProvider())
    results = await second.search("Tell me about coding")
    await second_engine.dispose()

    assert results[0].content == "Python is a language"
