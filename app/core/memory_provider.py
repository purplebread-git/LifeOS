from abc import ABC, abstractmethod

from app.models.memory import MemoryEntry


class MemoryProvider(ABC):
    @abstractmethod
    async def add(self, entry: MemoryEntry) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, entry_id: str) -> MemoryEntry | None:
        raise NotImplementedError

    @abstractmethod
    async def update(self, entry: MemoryEntry) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, entry_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        raise NotImplementedError