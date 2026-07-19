from app.knowledge.in_memory_knowledge_provider import InMemoryKnowledgeProvider
from app.models.knowledge import KnowledgeChunk


async def test_add_and_search_returns_chunk() -> None:
    provider = InMemoryKnowledgeProvider()
    await provider.add(
        KnowledgeChunk(id="1", content="Python is a programming language", source="wiki")
    )

    results = await provider.search("programming")

    assert len(results) == 1
    assert results[0].content == "Python is a programming language"
    assert results[0].source == "wiki"


async def test_search_is_case_insensitive() -> None:
    provider = InMemoryKnowledgeProvider()
    await provider.add(KnowledgeChunk(id="1", content="The Eiffel Tower is in Paris", source="doc"))

    results = await provider.search("eiffel")

    assert len(results) == 1


async def test_search_no_match_returns_empty() -> None:
    provider = InMemoryKnowledgeProvider()
    await provider.add(KnowledgeChunk(id="1", content="unrelated", source="doc"))

    assert await provider.search("missing") == []


async def test_add_batch_stores_all() -> None:
    provider = InMemoryKnowledgeProvider()
    await provider.add_batch(
        [
            KnowledgeChunk(id="1", content="alpha topic", source="a"),
            KnowledgeChunk(id="2", content="alpha again", source="b"),
        ]
    )

    results = await provider.search("alpha")

    assert len(results) == 2


async def test_search_respects_limit() -> None:
    provider = InMemoryKnowledgeProvider()
    await provider.add_batch(
        [KnowledgeChunk(id=str(i), content=f"topic {i}", source="s") for i in range(6)]
    )

    results = await provider.search("topic", limit=3)

    assert len(results) == 3


async def test_add_same_id_overwrites() -> None:
    provider = InMemoryKnowledgeProvider()
    await provider.add(KnowledgeChunk(id="1", content="old content", source="s"))
    await provider.add(KnowledgeChunk(id="1", content="new content", source="s"))

    results = await provider.search("content")

    assert len(results) == 1
    assert results[0].content == "new content"


async def test_list_sources_unique_and_sorted() -> None:
    provider = InMemoryKnowledgeProvider()
    await provider.add_batch(
        [
            KnowledgeChunk(id="1", content="a", source="zeta"),
            KnowledgeChunk(id="2", content="b", source="alpha"),
            KnowledgeChunk(id="3", content="c", source="alpha"),
        ]
    )

    assert await provider.list_sources() == ["alpha", "zeta"]


async def test_list_sources_empty() -> None:
    provider = InMemoryKnowledgeProvider()

    assert await provider.list_sources() == []


async def test_delete_source_removes_only_its_chunks() -> None:
    provider = InMemoryKnowledgeProvider()
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


async def test_delete_source_is_idempotent() -> None:
    provider = InMemoryKnowledgeProvider()
    await provider.add(KnowledgeChunk(id="1", content="x", source="a"))

    assert await provider.delete_source("missing") == 0
    assert await provider.delete_source("a") == 1
    assert await provider.delete_source("a") == 0
