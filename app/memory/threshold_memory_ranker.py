"""ThresholdMemoryRanker — первая стратегия ранжирования.

Политика (целиком внутри ranker, провайдер о ней не знает):
  * semantic-кандидаты проходят, только если score >= min_score (отсекает шум);
  * substring-кандидаты (точное совпадение на записи без эмбеддинга) проходят
    всегда — семантический порог к ним не применяется;
  * порядок: threshold → sort (semantic по score убыв.) → limit.

Лимит применяется ПОСЛЕ порога и сортировки, иначе слабые совпадения могут
вытеснить сильные ещё до отсечения.
"""

from __future__ import annotations

from app.core.memory_ranker import MemoryRanker
from app.models.memory import MemoryEntry, MemoryMatch

DEFAULT_SIMILARITY_THRESHOLD = 0.25


class ThresholdMemoryRanker(MemoryRanker):
    def __init__(self, min_score: float = DEFAULT_SIMILARITY_THRESHOLD) -> None:
        self._min_score = min_score

    def rank(self, matches: list[MemoryMatch], limit: int) -> list[MemoryEntry]:
        semantic = [
            match
            for match in matches
            if match.match_type == "semantic" and match.score >= self._min_score
        ]
        substring = [match for match in matches if match.match_type == "substring"]

        semantic.sort(key=lambda match: match.score, reverse=True)

        ordered = semantic + substring
        return [match.entry for match in ordered[:limit]]
