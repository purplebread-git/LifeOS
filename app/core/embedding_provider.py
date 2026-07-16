"""EmbeddingProvider — контракт генерации векторных представлений текста.

Абстракция появляется до второй реализации осознанно: OpenAI, Ollama,
SentenceTransformers, Voyage и т.п. — это разные инфраструктурные провайдеры
одной способности. Домен и память зависят только от этого контракта.
"""

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError
