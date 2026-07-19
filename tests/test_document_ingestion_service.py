from app.knowledge.document_ingestion_service import DocumentIngestionService
from app.knowledge.fixed_size_chunker import FixedSizeChunker
from app.knowledge.in_memory_knowledge_provider import InMemoryKnowledgeProvider
from app.knowledge.plain_text_extractor import PlainTextExtractor


def _service(
    provider: InMemoryKnowledgeProvider,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> DocumentIngestionService:
    return DocumentIngestionService(
        extractor=PlainTextExtractor(),
        chunker=FixedSizeChunker(chunk_size=chunk_size, overlap=overlap),
        knowledge_provider=provider,
    )


async def test_ingest_extracts_chunks_and_stores() -> None:
    # End-to-end pipeline: bytes → extract → split → add_batch → searchable.
    provider = InMemoryKnowledgeProvider()
    service = _service(provider)

    chunks = await service.ingest(b"LifeOS is a modular agent platform", source="handbook")

    assert len(chunks) == 1
    assert chunks[0].source == "handbook"
    stored = await provider.search("modular")
    assert stored[0].content == "LifeOS is a modular agent platform"


async def test_ingest_splits_long_document_into_multiple_chunks() -> None:
    provider = InMemoryKnowledgeProvider()
    service = _service(provider, chunk_size=10, overlap=2)

    chunks = await service.ingest(b"a b c d e f g h", source="doc")

    assert len(chunks) > 1
    assert all(chunk.source == "doc" for chunk in chunks)


async def test_ingest_empty_document_stores_nothing() -> None:
    provider = InMemoryKnowledgeProvider()
    service = _service(provider)

    chunks = await service.ingest(b"", source="doc")

    assert chunks == []
    assert await provider.search("anything") == []


async def test_ingest_whitespace_document_stores_nothing() -> None:
    provider = InMemoryKnowledgeProvider()
    service = _service(provider)

    chunks = await service.ingest(b"   \n\t  ", source="doc")

    assert chunks == []


async def test_ingest_passes_metadata_through() -> None:
    provider = InMemoryKnowledgeProvider()
    service = _service(provider)

    chunks = await service.ingest(b"hello world", source="doc", metadata={"lang": "en"})

    assert chunks[0].metadata["lang"] == "en"
    assert chunks[0].metadata["chunk_index"] == 0
