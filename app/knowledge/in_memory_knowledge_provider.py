"""InMemoryKnowledgeProvider — реализация KnowledgeProvider в оперативной
памяти процесса. Substring-поиск. Годится, чтобы доказать retrieval pipeline
(Knowledge → Context → LLM) отдельно от хранения; не переживает перезапуск.

Semantic-поиск (embeddings + cosine) и persistence — отдельные шаги, как это
было с памятью (InMemory substring → persistent → semantic).
"""

from __future__ import annotations

from app.core.knowledge_provider import KnowledgeProvider
from app.models.knowledge import KnowledgeChunk


class InMemoryKnowledgeProvider(KnowledgeProvider):
    def __init__(self) -> None:
        self._storage: dict[str, KnowledgeChunk] = {}

    async def add(self, chunk: KnowledgeChunk) -> None:
        self._storage[chunk.id] = chunk

    async def add_batch(self, chunks: list[KnowledgeChunk]) -> None:
        for chunk in chunks:
            self._storage[chunk.id] = chunk

    async def search(self, query: str, limit: int = 5) -> list[KnowledgeChunk]:
        matches = [c for c in self._storage.values() if query.lower() in c.content.lower()]
        return matches[:limit]
