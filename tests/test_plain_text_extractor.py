import pytest

from app.knowledge.plain_text_extractor import PlainTextExtractor


async def test_extracts_utf8_text() -> None:
    extractor = PlainTextExtractor()

    text = await extractor.extract(b"hello world")

    assert text == "hello world"


async def test_extracts_non_ascii() -> None:
    extractor = PlainTextExtractor()

    text = await extractor.extract("привет мир".encode())

    assert text == "привет мир"


async def test_empty_bytes_returns_empty_string() -> None:
    extractor = PlainTextExtractor()

    assert await extractor.extract(b"") == ""


async def test_invalid_utf8_raises() -> None:
    extractor = PlainTextExtractor()

    with pytest.raises(UnicodeDecodeError):
        await extractor.extract(b"\xff\xfe")
