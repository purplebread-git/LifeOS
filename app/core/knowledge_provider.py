"""KnowledgeProvider — контракт источника знаний (Knowledge Base / RAG).

Симметрично MemoryProvider, но над своей доменной сущностью (KnowledgeChunk).
search() возвращает list[KnowledgeChunk], а не list[str]: атрибуция источника
и метаданные нужны для цитирования и будущего scoring — строка стала бы
архитектурным долгом.

Ingestion в этом контракте — только add/add_batch готовых чанков. Chunking,
парсинг документов и загрузка файлов сюда НЕ входят (отдельная подсистема).

Управление вокруг source (list_sources/delete_source) — доменная модель Knowledge
организована вокруг источника. delete_source идемпотентен: несуществующий
источник → 0, без исключения.
"""

from abc import ABC, abstractmethod

from app.models.knowledge import KnowledgeChunk


class KnowledgeProvider(ABC):
    @abstractmethod
    async def add(self, chunk: KnowledgeChunk) -> None:
        raise NotImplementedError

    @abstractmethod
    async def add_batch(self, chunks: list[KnowledgeChunk]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> list[KnowledgeChunk]:
        raise NotImplementedError

    @abstractmethod
    async def list_sources(self) -> list[str]:
        """Уникальные имена источников, отсортированные по алфавиту."""
        raise NotImplementedError

    @abstractmethod
    async def delete_source(self, source: str) -> int:
        """Удаляет все чанки источника. Возвращает число удалённых.

        Идемпотентен: несуществующий источник → 0, без исключения.
        """
        raise NotImplementedError
