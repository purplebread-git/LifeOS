"""Архитектурный инвариант всей подсистемы extractor'ов, а не отдельного формата.

Любой формат (текстовый или бинарный) после DocumentIngestionService приходит
в одно и то же «представление» — обычный текст, одинаково пригодный для
дальнейшего пайплайна (chunker → knowledge). Байтовое совпадение не требуется;
требуется совпадение «языка общения» с системой.
"""

from app.knowledge.document_ingestion_service import DocumentIngestionService
from app.knowledge.extractor_registry import ExtractorRegistry
from app.knowledge.fixed_size_chunker import FixedSizeChunker
from app.knowledge.in_memory_knowledge_provider import InMemoryKnowledgeProvider
from app.knowledge.markdown_extractor import MarkdownExtractor
from app.knowledge.pdf_extractor import PdfExtractor
from app.knowledge.plain_text_extractor import PlainTextExtractor
from tests.pdf_fixtures import make_text_pdf


def _service(provider: InMemoryKnowledgeProvider) -> DocumentIngestionService:
    markdown = MarkdownExtractor()
    return DocumentIngestionService(
        extractor_registry=ExtractorRegistry(
            default=PlainTextExtractor(),
            extractors={
                ".md": markdown,
                ".markdown": markdown,
                ".pdf": PdfExtractor(),
            },
        ),
        chunker=FixedSizeChunker(),
        knowledge_provider=provider,
    )


async def test_markdown_and_pdf_yield_same_text_representation() -> None:
    sentence = "LifeOS is a modular agent platform"

    markdown_provider = InMemoryKnowledgeProvider()
    md_chunks = await _service(markdown_provider).ingest(
        f"# Title\n\n{sentence}.".encode(),
        source="README.md",
    )

    pdf_provider = InMemoryKnowledgeProvider()
    pdf_chunks = await _service(pdf_provider).ingest(
        make_text_pdf(["Title", f"{sentence}."]),
        source="manual.pdf",
    )

    # Оба формата свелись к одному и тому же обычному тексту.
    assert md_chunks[0].content == "Title LifeOS is a modular agent platform."
    assert pdf_chunks[0].content == "Title LifeOS is a modular agent platform."
    assert md_chunks[0].content == pdf_chunks[0].content


async def test_all_extractors_return_str() -> None:
    # Общий "язык" контракта: bytes → str, независимо от формата.
    plain = await PlainTextExtractor().extract(b"plain")
    markdown = await MarkdownExtractor().extract(b"# md")
    pdf = await PdfExtractor().extract(make_text_pdf(["pdf"]))

    assert isinstance(plain, str)
    assert isinstance(markdown, str)
    assert isinstance(pdf, str)
