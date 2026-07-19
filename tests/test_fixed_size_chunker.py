import pytest

from app.knowledge.fixed_size_chunker import FixedSizeChunker


def test_empty_text_returns_no_chunks() -> None:
    chunker = FixedSizeChunker(chunk_size=10, overlap=2)

    assert chunker.split("", source="doc") == []


def test_whitespace_only_returns_no_chunks() -> None:
    chunker = FixedSizeChunker(chunk_size=10, overlap=2)

    assert chunker.split("   \n\t  ", source="doc") == []


def test_short_text_is_single_chunk() -> None:
    chunker = FixedSizeChunker(chunk_size=100, overlap=10)

    chunks = chunker.split("hello world", source="doc")

    assert len(chunks) == 1
    assert chunks[0].content == "hello world"
    assert chunks[0].source == "doc"
    assert chunks[0].metadata["chunk_index"] == 0


def test_splits_into_multiple_chunks() -> None:
    chunker = FixedSizeChunker(chunk_size=5, overlap=2)

    chunks = chunker.split("a b c d e", source="doc")

    assert len(chunks) > 1
    assert [c.metadata["chunk_index"] for c in chunks] == list(range(len(chunks)))


def test_chunk_size_invariant_always_holds() -> None:
    chunker = FixedSizeChunker(chunk_size=20, overlap=5)
    text = " ".join(f"word{i}" for i in range(200))

    chunks = chunker.split(text, source="doc")

    assert chunks
    assert all(len(c.content) <= 20 for c in chunks)


def test_no_word_is_split_when_words_fit() -> None:
    chunker = FixedSizeChunker(chunk_size=10, overlap=3)

    chunks = chunker.split("alpha beta gamma delta", source="doc")

    # Ни один чанк не начинается/заканчивается обрезанным словом.
    words = {"alpha", "beta", "gamma", "delta"}
    for chunk in chunks:
        for token in chunk.content.split():
            assert token in words


def test_oversized_word_is_hard_split_to_respect_chunk_size() -> None:
    # Единственное слово длиннее chunk_size: инвариант важнее сохранения слова.
    chunker = FixedSizeChunker(chunk_size=4, overlap=1)

    chunks = chunker.split("abcdefghij", source="doc")

    assert all(len(c.content) <= 4 for c in chunks)
    assert "".join(c.content for c in chunks) == "abcdefghij"


def test_overlap_shares_content_between_consecutive_chunks() -> None:
    chunker = FixedSizeChunker(chunk_size=5, overlap=2)

    chunks = chunker.split("a b c d e f", source="doc")

    # Хвост предыдущего чанка встречается в начале следующего.
    first_words = chunks[0].content.split()
    second_words = chunks[1].content.split()
    assert first_words[-1] == second_words[0]


def test_ids_are_deterministic_across_calls() -> None:
    chunker = FixedSizeChunker(chunk_size=5, overlap=2)

    first = chunker.split("a b c d e", source="doc")
    second = chunker.split("a b c d e", source="doc")

    assert [c.id for c in first] == [c.id for c in second]


def test_same_content_same_id_different_content_different_id() -> None:
    chunker = FixedSizeChunker(chunk_size=100, overlap=0)

    same_a = chunker.split("hello world", source="doc")[0]
    same_b = chunker.split("hello world", source="doc")[0]
    other = chunker.split("goodbye world", source="doc")[0]

    assert same_a.id == same_b.id
    assert same_a.id != other.id


def test_id_depends_on_source() -> None:
    chunker = FixedSizeChunker(chunk_size=100, overlap=0)

    a = chunker.split("hello world", source="doc-a")[0]
    b = chunker.split("hello world", source="doc-b")[0]

    assert a.id != b.id


def test_metadata_is_merged_with_chunk_index() -> None:
    chunker = FixedSizeChunker(chunk_size=100, overlap=0)

    chunks = chunker.split("hello world", source="doc", metadata={"lang": "en"})

    assert chunks[0].metadata == {"lang": "en", "chunk_index": 0}


def test_invalid_chunk_size_raises() -> None:
    with pytest.raises(ValueError):
        FixedSizeChunker(chunk_size=0, overlap=0)


def test_overlap_not_less_than_chunk_size_raises() -> None:
    with pytest.raises(ValueError):
        FixedSizeChunker(chunk_size=5, overlap=5)


def test_negative_overlap_raises() -> None:
    with pytest.raises(ValueError):
        FixedSizeChunker(chunk_size=5, overlap=-1)
