from app.memory.threshold_memory_ranker import ThresholdMemoryRanker
from app.models.memory import MemoryEntry, MemoryMatch


def _match(entry_id: str, score: float, match_type: str) -> MemoryMatch:
    return MemoryMatch(
        entry=MemoryEntry(id=entry_id, content=f"memory {entry_id}"),
        score=score,
        match_type=match_type,  # type: ignore[arg-type]
    )


def test_semantic_below_threshold_is_filtered() -> None:
    ranker = ThresholdMemoryRanker(min_score=0.25)

    result = ranker.rank([_match("weak", 0.1, "semantic")], limit=5)

    assert result == []


def test_semantic_at_or_above_threshold_passes() -> None:
    ranker = ThresholdMemoryRanker(min_score=0.25)

    result = ranker.rank([_match("edge", 0.25, "semantic")], limit=5)

    assert [entry.id for entry in result] == ["edge"]


def test_threshold_filters_semantic_but_not_substring() -> None:
    # Самый важный бизнес-кейс: семантический порог отсекает слабый semantic-хит,
    # но substring-совпадение (точное, на записи без эмбеддинга) сохраняется.
    ranker = ThresholdMemoryRanker(min_score=0.25)

    result = ranker.rank(
        [
            _match("weak-semantic", 0.1, "semantic"),
            _match("exact-substring", 0.0, "substring"),
        ],
        limit=5,
    )

    assert [entry.id for entry in result] == ["exact-substring"]


def test_ranker_applies_limit_after_ranking() -> None:
    # Порядок обязан быть threshold → sort → limit. Если лимит применить раньше,
    # слабые совпадения могут вытеснить сильные до отсечения/сортировки.
    ranker = ThresholdMemoryRanker(min_score=0.25)

    result = ranker.rank(
        [
            _match("low", 0.3, "semantic"),
            _match("high", 0.9, "semantic"),
            _match("mid", 0.6, "semantic"),
        ],
        limit=2,
    )

    assert [entry.id for entry in result] == ["high", "mid"]


def test_semantic_sorted_by_score_descending() -> None:
    ranker = ThresholdMemoryRanker(min_score=0.0)

    result = ranker.rank(
        [
            _match("a", 0.4, "semantic"),
            _match("b", 0.8, "semantic"),
            _match("c", 0.6, "semantic"),
        ],
        limit=5,
    )

    assert [entry.id for entry in result] == ["b", "c", "a"]


def test_semantic_ordered_before_substring() -> None:
    ranker = ThresholdMemoryRanker(min_score=0.25)

    result = ranker.rank(
        [
            _match("sub", 0.0, "substring"),
            _match("sem", 0.9, "semantic"),
        ],
        limit=5,
    )

    assert [entry.id for entry in result] == ["sem", "sub"]


def test_empty_candidates_returns_empty() -> None:
    ranker = ThresholdMemoryRanker(min_score=0.25)

    assert ranker.rank([], limit=5) == []
