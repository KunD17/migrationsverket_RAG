"""Checks whether retrieved chunks are relevant enough to answer the query."""

from __future__ import annotations

from typing import Sequence

import requests

from migrationsverket_bot.config import OLLAMA_MODEL, OLLAMA_BASE_URL


def assess_relevance(query: str, chunks: Sequence[dict]) -> float:
    """Return a 0–1 relevance score for retrieved chunks relative to the query."""
    if not chunks:
        return 0.0

    chunk_texts = "\n\n".join(
        c.get("document", c.get("text", "")) for c in chunks[:3]
    )
    prompt = (
        "You are evaluating whether retrieved text chunks contain enough information "
        "to answer a question about Swedish immigration.\n\n"
        f"Question: {query}\n\n"
        f"Retrieved chunks:\n{chunk_texts}\n\n"
        "On a scale from 0.0 to 1.0, how well do these chunks answer the question? "
        "Reply with only a single decimal number between 0.0 and 1.0."
    )

    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=60,
    )
    response.raise_for_status()
    text = response.json()["response"].strip()

    try:
        score = float(text.split()[0].rstrip(".,)"))
        return min(max(score, 0.0), 1.0)
    except (ValueError, IndexError):
        return 0.5
