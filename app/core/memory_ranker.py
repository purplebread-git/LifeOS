from abc import ABC, abstractmethod

from app.models.memory import MemoryEntry, MemoryMatch


class MemoryRanker(ABC):
    """Стратегия ранжирования кандидатов памяти.

    Retrieval-провайдер собирает кандидатов (MemoryMatch со score и типом
    совпадения), а ranker решает политику: порог, сортировку, лимит, будущие
    веса (recency, substring bonus, hybrid). Провайдер не знает о политике —
    это позволяет менять стратегию, не трогая storage.
    """

    @abstractmethod
    def rank(self, matches: list[MemoryMatch], limit: int) -> list[MemoryEntry]:
        raise NotImplementedError
