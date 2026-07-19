from abc import ABC, abstractmethod

from app.models.knowledge import KnowledgeChunk, KnowledgeMatch


class KnowledgeRanker(ABC):
    """Стратегия ранжирования кандидатов знаний.

    Симметрична MemoryRanker, но остаётся отдельной абстракцией: память и
    знания — независимо эволюционирующие подсистемы. Обобщение (Ranker[T])
    отложено до появления третьего независимого потребителя ранжирования.

    В сигнатуре нет threshold/min_score намеренно: следующий ранкер может
    использовать MMR, recency, citation weight, source priority — интерфейс
    при этом не меняется.
    """

    @abstractmethod
    def rank(self, matches: list[KnowledgeMatch], limit: int) -> list[KnowledgeChunk]:
        raise NotImplementedError
