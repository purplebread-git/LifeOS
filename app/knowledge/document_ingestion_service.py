"""DocumentIngestionService — тонкая оркестрация загрузки документа в знания.

Сценарий один и максимально «тупой»:
    extract → strip → (пусто → []) → split → add_batch → return

Сервис НЕ знает про формат (это внутри extractor) и НЕ содержит бизнес-логики
сверх оркестрации: ни логирования, ни retries, ни dedup, ни merge policy, ни
progress-callbacks. Всё это — при необходимости — добавляется позже, не ломая
контракт.

Выбор extractor'а по source делегирован ExtractorRegistry. Архитектурный
инвариант: добавление нового формата = запись в реестре + новый
DocumentExtractor, БЕЗ изменений в этом сервисе.
"""

from __future__ import annotations

from typing import Any

from app.core.chunker import Chunker
from app.core.knowledge_provider import KnowledgeProvider
from app.knowledge.extractor_registry import ExtractorRegistry
from app.models.knowledge import KnowledgeChunk


class DocumentIngestionService:
    def __init__(
        self,
        extractor_registry: ExtractorRegistry,
        chunker: Chunker,
        knowledge_provider: KnowledgeProvider,
    ) -> None:
        self._extractor_registry = extractor_registry
        self._chunker = chunker
        self._knowledge_provider = knowledge_provider

    async def ingest(
        self,
        content: bytes,
        source: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[KnowledgeChunk]:
        extractor = self._extractor_registry.resolve(source)
        text = await extractor.extract(content)
        if not text.strip():
            return []

        chunks = self._chunker.split(text, source, metadata)
        await self._knowledge_provider.add_batch(chunks)
        return chunks
