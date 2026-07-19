"""PlainTextExtractor — извлечение текста из простых текстовых файлов.

Декодирует байты как UTF-8. Markdown/PDF/DOCX/HTML — отдельные адаптеры за тем
же контрактом (не в этом PR): задача — доказать ingestion pipeline, а не
поддержку форматов.
"""

from __future__ import annotations

from app.core.document_extractor import DocumentExtractor


class PlainTextExtractor(DocumentExtractor):
    async def extract(self, content: bytes) -> str:
        return content.decode("utf-8")
