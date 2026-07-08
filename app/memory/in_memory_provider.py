"""InMemoryMemoryProvider — реализация MemoryProvider в оперативной памяти
процесса. Годится для разработки и тестов; не переживает перезапуск."""

from __future__ import annotations

from app.core.memory_provider import MemoryProvider
from app.models.memory import MemoryEntry


class InMemoryMemoryProvider(MemoryProvider):
    def __init__(self) -> None:
        self._storage: dict[str, MemoryEntry] = {}

    async def add(self, entry: MemoryEntry) -> None:
        self._storage[entry.id] = entry

    async def get(self, entry_id: str) -> MemoryEntry | None:
        return self._storage.get(entry_id)

    async def update(self, entry: MemoryEntry) -> None:
        self._storage[entry.id] = entry

    async def delete(self, entry_id: str) -> None:
        self._storage.pop(entry_id, None)

    async def search(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        matches = [e for e in self._storage.values() if query.lower() in e.content.lower()]
        return matches[:limit]
