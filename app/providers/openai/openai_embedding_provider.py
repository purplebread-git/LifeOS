"""OpenAIEmbeddingProvider — реализация EmbeddingProvider поверх OpenAIClient."""

from __future__ import annotations

from app.core.embedding_provider import EmbeddingProvider
from app.providers.openai.openai_client import OpenAIClient


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, client: OpenAIClient, model: str) -> None:
        self._client = client
        self._model = model

    async def embed(self, text: str) -> list[float]:
        vectors = await self._client.embed(self._model, [text])
        return vectors[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await self._client.embed(self._model, texts)
