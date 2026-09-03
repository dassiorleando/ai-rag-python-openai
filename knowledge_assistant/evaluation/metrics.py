"""Small, dependency-free information-retrieval metrics."""

from __future__ import annotations

from collections.abc import Sequence, Set


def recall_at_k(retrieved: Sequence[str], relevant: Set[str], k: int) -> float:
    """Fraction of relevant sources found in the first ``k`` results."""
    if k < 1:
        raise ValueError("k must be greater than zero")
    if not relevant:
        raise ValueError("recall_at_k is undefined when there are no relevant items")
    return len(set(retrieved[:k]) & relevant) / len(relevant)


def reciprocal_rank(retrieved: Sequence[str], relevant: Set[str]) -> float:
    """Inverse rank of the first relevant result, or zero if none is present."""
    for rank, item in enumerate(retrieved, start=1):
        if item in relevant:
            return 1.0 / rank
    return 0.0
