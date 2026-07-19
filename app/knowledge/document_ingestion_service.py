"""DocumentIngestionService — тонкая оркестрация загрузки документа в знания.

Сценарий один и максимально «тупой»:
    extract → strip → (пусто → []) → split → add_batch → return

Сервис НЕ знает про формат (это внутри extractor) и НЕ содержит бизнес-логики
сверх оркестрации: ни логирования, ни retries, ни dedup, ни merge policy, ни
progress-callbacks. Всё это — при необходимости — добавляется позже, не ломая
контракт. Добавление нового формата = регистрация нового DocumentExtractor,
без изменений здесь.
"""

from __future__ import annotations

from typing import Any

from app.core.chunker import Chunker
from app.core.document_extractor import DocumentExtractor
from app.core.knowledge_provider import KnowledgeProvider
from app.models.knowledge import KnowledgeChunk


class DocumentIngestionService:
    def __init__(
        self,
        extractor: DocumentExtractor,
        chunker: Chunker,
        knowledge_provider: KnowledgeProvider,
    ) -> None:
        self._extractor = extractor
        self._chunker = chunker
        self._knowledge_provider = knowledge_provider

    async def ingest(
        self,
        content: bytes,
        source: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[KnowledgeChunk]:
        text = await self._extractor.extract(content)
        if not text.strip():
            return []

        chunks = self._chunker.split(text, source, metadata)
        await self._knowledge_provider.add_batch(chunks)
        return chunks
