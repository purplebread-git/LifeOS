"""ThresholdKnowledgeRanker — первая стратегия ранжирования знаний.

Политика зеркальна ThresholdMemoryRanker, чтобы поведение Memory и Knowledge
было одинаково предсказуемым:
  * semantic-кандидаты проходят, только если score >= min_score (отсекает шум);
  * substring-кандидаты (точное совпадение на чанке без эмбеддинга) проходят
    всегда — семантический порог к ним не применяется;
  * порядок: threshold → sort (semantic по score убыв.) → append substring → limit.

Лимит применяется ПОСЛЕ порога и сортировки, иначе слабые совпадения могут
вытеснить сильные ещё до отсечения.
"""

from __future__ import annotations

from app.core.knowledge_ranker import KnowledgeRanker
from app.models.knowledge import KnowledgeChunk, KnowledgeMatch

DEFAULT_SIMILARITY_THRESHOLD = 0.25


class ThresholdKnowledgeRanker(KnowledgeRanker):
    def __init__(self, min_score: float = DEFAULT_SIMILARITY_THRESHOLD) -> None:
        self._min_score = min_score

    def rank(self, matches: list[KnowledgeMatch], limit: int) -> list[KnowledgeChunk]:
        semantic = [
            match
            for match in matches
            if match.match_type == "semantic" and match.score >= self._min_score
        ]
        substring = [match for match in matches if match.match_type == "substring"]

        semantic.sort(key=lambda match: match.score, reverse=True)

        ordered = semantic + substring
        return [match.chunk for match in ordered[:limit]]
