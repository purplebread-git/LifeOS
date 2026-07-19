"""ExtractorRegistry — выбор DocumentExtractor по источнику.

Роутинг живёт здесь (а не в сервисе и не в самом extractor'е): реестр знает
source, extractor остаётся узким (bytes → text и ничего про формат-роутинг).

Ключ — расширение файла из source (`.md`, `.pdf`, ...), регистронезависимо;
неизвестное расширение или его отсутствие → default (PlainTextExtractor).

Архитектурный инвариант: после появления реестра DocumentIngestionService
больше не меняется при добавлении новых форматов — новый формат = новая запись
в реестре + новый DocumentExtractor.
"""

from __future__ import annotations

from pathlib import PurePosixPath

from app.core.document_extractor import DocumentExtractor


class ExtractorRegistry:
    def __init__(
        self,
        default: DocumentExtractor,
        extractors: dict[str, DocumentExtractor] | None = None,
    ) -> None:
        self._default = default
        self._extractors = {ext.lower(): extractor for ext, extractor in (extractors or {}).items()}

    def resolve(self, source: str) -> DocumentExtractor:
        suffix = PurePosixPath(source).suffix.lower()
        return self._extractors.get(suffix, self._default)
