"""Векторные метрики похожести. Чистые функции, без внешних зависимостей."""

from __future__ import annotations

import math


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Косинусная близость двух векторов в диапазоне [-1, 1].

    Возвращает 0.0 для пустых, разной длины или нулевых векторов —
    защита от деления на ноль и рассинхрона размерностей."""
    if not a or not b or len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot / (norm_a * norm_b)
