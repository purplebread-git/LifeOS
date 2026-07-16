"""KnowledgeProvider — контракт источника знаний (Knowledge Base / RAG).

Задел под будущее: контракт зафиксирован СЕЙЧАС, чтобы при подключении
знания (KnowledgeContextLayer → KnowledgeProvider → VectorStore) не
рефакторить уже существующий слой. Реализации, DI-регистрации и
использования пока нет — только абстракция.
"""

from abc import ABC, abstractmethod


class KnowledgeProvider(ABC):
    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> list[str]:
        raise NotImplementedError
