"""Chunker — контракт нарезки текста на KnowledgeChunk'и.

Абстракция появляется из-за различия ПОВЕДЕНИЯ, а не ради единообразия:
разные стратегии (FixedSize, Sentence, Paragraph, Recursive, Token, Semantic)
дают разные чанки при одном входе. Ingestion (#19) зависит от способности
`split(...)`, а не от конкретной стратегии — как и остальные подсистемы
зависят от EmbeddingProvider / MemoryProvider / KnowledgeProvider / *Ranker.

Метод назван `split`, а не `chunk`, чтобы не было тавтологии chunker.chunk().
"""

from abc import ABC, abstractmethod
from typing import Any

from app.models.knowledge import KnowledgeChunk


class Chunker(ABC):
    @abstractmethod
    def split(
        self,
        text: str,
        source: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[KnowledgeChunk]:
        raise NotImplementedError
