"""Checks whether retrieved chunks are relevant enough to answer the query."""

from __future__ import annotations

from typing import Sequence


def assess_relevance(query: str, chunks: Sequence[dict]) -> float:
    """Return a 0–1 relevance score based on average cosine similarity of top chunks."""
    if not chunks:
        return 0.0
    scores = [c["confidence"] for c in chunks[:3] if "confidence" in c]
    return sum(scores) / len(scores) if scores else 0.0
