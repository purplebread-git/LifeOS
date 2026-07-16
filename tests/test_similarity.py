from app.memory.similarity import cosine_similarity


def test_identical_vectors() -> None:
    assert cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == 1.0


def test_orthogonal_vectors() -> None:
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_opposite_vectors() -> None:
    assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == -1.0


def test_zero_vector_returns_zero() -> None:
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_length_mismatch_returns_zero() -> None:
    assert cosine_similarity([1.0, 2.0], [1.0]) == 0.0


def test_empty_returns_zero() -> None:
    assert cosine_similarity([], []) == 0.0
