"""SemanticSqliteKnowledgeProvider — persistent knowledge (SQLite) с semantic-поиском.

Симметрично SemanticSqliteMemoryProvider: контент, source и метаданные
сохраняются всегда, дополнительно хранится эмбеддинг чанка, поиск идёт по
косинусной близости.

Устойчивость к сбоям embeddings — обязательное требование (как у памяти):
  * add/add_batch: чанк сохраняется даже если эмбеддинг получить не удалось
    (embedding = NULL);
  * search: если эмбеддинг запроса получить не удалось — полный откат к
    substring; иначе semantic по чанкам с эмбеддингом + substring-добор для
    чанков с embedding IS NULL.

Ranking (порог/веса) здесь НЕ вводится — это отдельный этап (#17), как это
было у памяти (semantic → затем ranker). Наружу отдаётся list[KnowledgeChunk],
отсортированный по близости.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.embedding_provider import EmbeddingProvider
from app.core.exceptions import EmbeddingError
from app.core.knowledge_provider import KnowledgeProvider
from app.models.knowledge import KnowledgeChunk
from app.persistence.models import KnowledgeRecord
from app.utils.similarity import cosine_similarity


class SemanticSqliteKnowledgeProvider(KnowledgeProvider):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self._session_factory = session_factory
        self._embedding_provider = embedding_provider

    async def add(self, chunk: KnowledgeChunk) -> None:
        embedding = await self._safe_embed(chunk.content)
        async with self._session_factory() as session:
            await session.merge(_to_record(chunk, embedding))
            await session.commit()

    async def add_batch(self, chunks: list[KnowledgeChunk]) -> None:
        embeddings = [await self._safe_embed(chunk.content) for chunk in chunks]
        async with self._session_factory() as session:
            for chunk, embedding in zip(chunks, embeddings, strict=True):
                await session.merge(_to_record(chunk, embedding))
            await session.commit()

    async def search(self, query: str, limit: int = 5) -> list[KnowledgeChunk]:
        query_vec = await self._safe_embed(query)

        async with self._session_factory() as session:
            records = list((await session.execute(select(KnowledgeRecord))).scalars().all())

        if query_vec is None:
            # Полная деградация: эмбеддинг запроса недоступен → substring по всем.
            fallback = [r for r in records if query.lower() in r.content.lower()]
            return [_to_chunk(r) for r in fallback[:limit]]

        scored: list[tuple[KnowledgeRecord, float]] = []
        substring_fallback: list[KnowledgeRecord] = []
        for record in records:
            if record.embedding:
                score = cosine_similarity(query_vec, record.embedding)
                scored.append((record, score))
            elif query.lower() in record.content.lower():
                substring_fallback.append(record)

        scored.sort(key=lambda pair: pair[1], reverse=True)
        ordered = [record for record, _ in scored] + substring_fallback
        return [_to_chunk(record) for record in ordered[:limit]]

    async def _safe_embed(self, text: str) -> list[float] | None:
        try:
            return await self._embedding_provider.embed(text)
        except EmbeddingError:
            return None


def _to_record(chunk: KnowledgeChunk, embedding: list[float] | None) -> KnowledgeRecord:
    return KnowledgeRecord(
        id=chunk.id,
        content=chunk.content,
        source=chunk.source,
        knowledge_metadata=chunk.metadata,
        embedding=embedding,
    )


def _to_chunk(record: KnowledgeRecord) -> KnowledgeChunk:
    return KnowledgeChunk(
        id=record.id,
        content=record.content,
        source=record.source,
        metadata=record.knowledge_metadata,
    )
