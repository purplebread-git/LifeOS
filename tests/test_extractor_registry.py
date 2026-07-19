from app.core.document_extractor import DocumentExtractor
from app.knowledge.extractor_registry import ExtractorRegistry
from app.knowledge.plain_text_extractor import PlainTextExtractor


class _StubExtractor(DocumentExtractor):
    def __init__(self, label: str) -> None:
        self.label = label

    async def extract(self, content: bytes) -> str:
        return self.label


def test_resolves_registered_extension() -> None:
    md = _StubExtractor("md")
    registry = ExtractorRegistry(default=PlainTextExtractor(), extractors={".md": md})

    assert registry.resolve("docs/api.md") is md


def test_falls_back_to_default_for_unknown_extension() -> None:
    default = PlainTextExtractor()
    registry = ExtractorRegistry(default=default, extractors={".md": _StubExtractor("md")})

    assert registry.resolve("notes.txt") is default


def test_falls_back_to_default_when_no_extension() -> None:
    default = PlainTextExtractor()
    registry = ExtractorRegistry(default=default, extractors={".md": _StubExtractor("md")})

    assert registry.resolve("handbook") is default


def test_extension_match_is_case_insensitive() -> None:
    md = _StubExtractor("md")
    registry = ExtractorRegistry(default=PlainTextExtractor(), extractors={".md": md})

    assert registry.resolve("README.MD") is md


def test_registered_extension_case_is_normalized() -> None:
    md = _StubExtractor("md")
    registry = ExtractorRegistry(default=PlainTextExtractor(), extractors={".MD": md})

    assert registry.resolve("file.md") is md


def test_default_only_registry_always_returns_default() -> None:
    default = PlainTextExtractor()
    registry = ExtractorRegistry(default=default)

    assert registry.resolve("file.md") is default
    assert registry.resolve("plain") is default
