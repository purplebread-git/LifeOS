"""FixedSizeChunker — нарезка текста фиксированного размера с overlap.

Простейшая стратегия: доказать архитектуру, а не выиграть в качестве
retrieval (sentence/recursive/semantic — будущие стратегии за тем же ABC).

Поведение (зафиксировано тестами):
  * greedy-упаковка по СЛОВАМ: чанки не начинаются и не заканчиваются посреди
    слова; пробелы нормализуются (последовательности whitespace → один пробел);
  * инвариант: len(content) <= chunk_size ВСЕГДА. Слово длиннее chunk_size
    режется жёстко (иначе chunk_size перестал бы быть настоящим ограничением);
  * overlap измеряется в символах и тоже выравнивается по границам слов;
  * пустой/whitespace-текст → []; текст короче chunk_size → один чанк;
  * id чанка детерминирован: sha256(source + content). Одинаковый чанк → тот же
    id; повторная загрузка того же документа → те же id; изменился текст → id
    меняется (устойчиво к сдвигам содержимого, в отличие от source#index).
"""

from __future__ import annotations

import hashlib
from typing import Any

from app.core.chunker import Chunker
from app.models.knowledge import KnowledgeChunk

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_OVERLAP = 200


class FixedSizeChunker(Chunker):
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if not 0 <= overlap < chunk_size:
            raise ValueError("overlap must satisfy 0 <= overlap < chunk_size")
        self._chunk_size = chunk_size
        self._overlap = overlap

    def split(
        self,
        text: str,
        source: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[KnowledgeChunk]:
        words = _normalize_words(text.split(), self._chunk_size)
        contents = _pack(words, self._chunk_size, self._overlap)

        base = metadata or {}
        return [
            KnowledgeChunk(
                id=_chunk_id(source, content),
                content=content,
                source=source,
                metadata={**base, "chunk_index": index},
            )
            for index, content in enumerate(contents)
        ]


def _normalize_words(words: list[str], chunk_size: int) -> list[str]:
    """Режет слова длиннее chunk_size на куски <= chunk_size (hard cut)."""
    out: list[str] = []
    for word in words:
        while len(word) > chunk_size:
            out.append(word[:chunk_size])
            word = word[chunk_size:]
        if word:
            out.append(word)
    return out


def _pack(words: list[str], chunk_size: int, overlap: int) -> list[str]:
    contents: list[str] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        if current and current_len + 1 + len(word) > chunk_size:
            contents.append(" ".join(current))
            tail = _overlap_tail(current, overlap)
            # progress guard: overlap не должен мешать поместить следующее слово,
            # иначе тот же чанк переиздавался бы бесконечно.
            if tail and _joined_len(tail) + 1 + len(word) > chunk_size:
                tail = []
            current = tail
            current_len = _joined_len(current)

        current_len = current_len + 1 + len(word) if current else len(word)
        current.append(word)

    if current:
        contents.append(" ".join(current))
    return contents


def _overlap_tail(words: list[str], overlap: int) -> list[str]:
    """Максимальный суффикс слов, чья длина в объединении <= overlap."""
    if overlap <= 0:
        return []
    tail: list[str] = []
    for word in reversed(words):
        if _joined_len([word, *tail]) > overlap:
            break
        tail.insert(0, word)
    return tail


def _joined_len(words: list[str]) -> int:
    if not words:
        return 0
    return sum(len(word) for word in words) + (len(words) - 1)


def _chunk_id(source: str, content: str) -> str:
    return hashlib.sha256(f"{source}\n{content}".encode()).hexdigest()
