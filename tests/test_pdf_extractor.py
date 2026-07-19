import pytest
from pdf_fixtures import make_text_pdf, make_textless_pdf
from pypdf.errors import PyPdfError

from app.knowledge.pdf_extractor import PdfExtractor


async def test_extracts_embedded_text() -> None:
    pdf = make_text_pdf(["Hello PDF world"])

    text = await PdfExtractor().extract(pdf)

    assert text == "Hello PDF world"


async def test_pages_are_joined_by_newline() -> None:
    pdf = make_text_pdf(["First page", "Second page"])

    text = await PdfExtractor().extract(pdf)

    assert text == "First page\nSecond page"


async def test_document_without_text_layer_returns_empty() -> None:
    # Скан без текстового слоя: OCR отсутствует → пустой результат.
    pdf = make_textless_pdf()

    text = await PdfExtractor().extract(pdf)

    assert text == ""


async def test_corrupt_pdf_raises() -> None:
    # Ошибки чтения PDF не подавляются (инфраструктурная ошибка pypdf).
    with pytest.raises(PyPdfError):
        await PdfExtractor().extract(b"not a pdf at all")
