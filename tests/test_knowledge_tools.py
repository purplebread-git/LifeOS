import pytest

from app.core.execution_context import ExecutionContext
from app.knowledge.document_ingestion_service import DocumentIngestionService
from app.knowledge.fixed_size_chunker import FixedSizeChunker
from app.knowledge.in_memory_knowledge_provider import InMemoryKnowledgeProvider
from app.knowledge.plain_text_extractor import PlainTextExtractor
from app.models.knowledge import KnowledgeChunk
from app.models.message import TextBlock
from app.tools.delete_source_tool import DeleteSourceTool
from app.tools.ingest_document_tool import IngestDocumentTool
from app.tools.list_sources_tool import ListSourcesTool
from app.tools.search_knowledge_tool import SearchKnowledgeTool


def _context(provider: InMemoryKnowledgeProvider) -> ExecutionContext:
    service = DocumentIngestionService(
        extractor=PlainTextExtractor(),
        chunker=FixedSizeChunker(),
        knowledge_provider=provider,
    )
    return ExecutionContext(
        conversation_id="test",
        knowledge=provider,
        ingestion=service,
    )


async def test_ingest_document_tool_stores_knowledge() -> None:
    provider = InMemoryKnowledgeProvider()
    tool = IngestDocumentTool()

    result = await tool.execute(
        {"content": "LifeOS is a modular agent platform", "source": "handbook"},
        _context(provider),
    )

    block = result.content[0]
    assert isinstance(block, TextBlock)
    assert "handbook" in block.text

    stored = await provider.search("modular")
    assert stored[0].content == "LifeOS is a modular agent platform"


async def test_agent_full_knowledge_cycle_ingest_then_search() -> None:
    # Замыкание контура: агент читает текст → сохраняет → находит знание.
    provider = InMemoryKnowledgeProvider()
    context = _context(provider)

    await IngestDocumentTool().execute(
        {"content": "The Eiffel Tower is located in Paris", "source": "geo"},
        context,
    )

    result = await SearchKnowledgeTool().execute(
        {"query": "Eiffel"},
        context,
    )

    block = result.content[0]
    assert isinstance(block, TextBlock)
    assert "Source: geo" in block.text
    assert "Eiffel Tower" in block.text


async def test_search_knowledge_tool_no_results() -> None:
    provider = InMemoryKnowledgeProvider()

    result = await SearchKnowledgeTool().execute(
        {"query": "missing"},
        _context(provider),
    )

    block = result.content[0]
    assert isinstance(block, TextBlock)
    assert block.text == "No knowledge found"


async def test_ingest_document_tool_requires_ingestion_capability() -> None:
    with pytest.raises(ValueError):
        await IngestDocumentTool().execute(
            {"content": "x", "source": "s"},
            ExecutionContext(conversation_id="test"),
        )


async def test_search_knowledge_tool_requires_knowledge_capability() -> None:
    with pytest.raises(ValueError):
        await SearchKnowledgeTool().execute(
            {"query": "x"},
            ExecutionContext(conversation_id="test"),
        )


async def test_list_sources_tool_lists_sources() -> None:
    provider = InMemoryKnowledgeProvider()
    await provider.add_batch(
        [
            KnowledgeChunk(id="1", content="a", source="zeta"),
            KnowledgeChunk(id="2", content="b", source="alpha"),
        ]
    )

    result = await ListSourcesTool().execute({}, _context(provider))

    block = result.content[0]
    assert isinstance(block, TextBlock)
    assert block.text == "- alpha\n- zeta"


async def test_list_sources_tool_empty() -> None:
    result = await ListSourcesTool().execute({}, _context(InMemoryKnowledgeProvider()))

    block = result.content[0]
    assert isinstance(block, TextBlock)
    assert block.text == "No sources"


async def test_delete_source_tool_reports_count() -> None:
    provider = InMemoryKnowledgeProvider()
    await provider.add_batch(
        [
            KnowledgeChunk(id="1", content="a", source="docs"),
            KnowledgeChunk(id="2", content="b", source="docs"),
        ]
    )

    result = await DeleteSourceTool().execute({"source": "docs"}, _context(provider))

    block = result.content[0]
    assert isinstance(block, TextBlock)
    assert "2 chunk(s)" in block.text
    assert "docs" in block.text
    assert await provider.list_sources() == []


async def test_delete_source_tool_idempotent_reports_zero() -> None:
    result = await DeleteSourceTool().execute(
        {"source": "missing"},
        _context(InMemoryKnowledgeProvider()),
    )

    block = result.content[0]
    assert isinstance(block, TextBlock)
    assert "0 chunk(s)" in block.text


async def test_list_sources_tool_requires_knowledge_capability() -> None:
    with pytest.raises(ValueError):
        await ListSourcesTool().execute({}, ExecutionContext(conversation_id="test"))


async def test_delete_source_tool_requires_knowledge_capability() -> None:
    with pytest.raises(ValueError):
        await DeleteSourceTool().execute(
            {"source": "x"},
            ExecutionContext(conversation_id="test"),
        )
