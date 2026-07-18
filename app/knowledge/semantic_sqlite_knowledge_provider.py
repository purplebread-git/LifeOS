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

Similarity score считается внутри (KnowledgeMatch), а политику отбора —
порог, сортировку, лимит — применяет инъектируемый KnowledgeRanker
(симметрично памяти). Контракт KnowledgeProvider.search() не меняется:
наружу отдаётся list[KnowledgeChunk].
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.embedding_provider import EmbeddingProvider
from app.core.exceptions import EmbeddingError
from app.core.knowledge_provider import KnowledgeProvider
from app.core.knowledge_ranker import KnowledgeRanker
from app.models.knowledge import KnowledgeChunk, KnowledgeMatch
from app.persistence.models import KnowledgeRecord
from app.utils.similarity import cosine_similarity

# Score-заглушка для substring-кандидатов (без эмбеддинга): семантический порог
# к ним не применяется, поэтому конкретное значение на ранжирование не влияет.
_SUBSTRING_FALLBACK_SCORE = 0.0


class SemanticSqliteKnowledgeProvider(KnowledgeProvider):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        embedding_provider: EmbeddingProvider,
        ranker: KnowledgeRanker,
    ) -> None:
        self._session_factory = session_factory
        self._embedding_provider = embedding_provider
        self._ranker = ranker

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
        matches = await self._collect_matches(query)
        return self._ranker.rank(matches, limit)

    async def _collect_matches(self, query: str) -> list[KnowledgeMatch]:
        """Собирает кандидатов со score и типом совпадения — без политики отбора.

        Порог/сортировку/лимит применяет ranker; провайдер лишь считает score.
        """
        query_vec = await self._safe_embed(query)

        async with self._session_factory() as session:
            records = list((await session.execute(select(KnowledgeRecord))).scalars().all())

        if query_vec is None:
            # Полная деградация: эмбеддинг запроса недоступен → substring по всем.
            return [
                KnowledgeMatch(
                    chunk=_to_chunk(record),
                    score=_SUBSTRING_FALLBACK_SCORE,
                    match_type="substring",
                )
                for record in records
                if query.lower() in record.content.lower()
            ]

        matches: list[KnowledgeMatch] = []
        for record in records:
            if record.embedding:
                score = cosine_similarity(query_vec, record.embedding)
                matches.append(
                    KnowledgeMatch(chunk=_to_chunk(record), score=score, match_type="semantic")
                )
            elif query.lower() in record.content.lower():
                matches.append(
                    KnowledgeMatch(
                        chunk=_to_chunk(record),
                        score=_SUBSTRING_FALLBACK_SCORE,
                        match_type="substring",
                    )
                )
        return matches

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
