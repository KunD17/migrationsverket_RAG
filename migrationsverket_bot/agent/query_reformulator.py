"""Reformulates queries when retrieval relevance is low."""

from __future__ import annotations

import requests

from migrationsverket_bot.config import OLLAMA_MODEL, OLLAMA_BASE_URL


def reformulate_query(original_query: str, feedback: str | None = None) -> str:
    """Return a reformulated query intended to improve retrieval results."""
    feedback_line = f"\nContext: {feedback}" if feedback else ""
    prompt = (
        "You are helping improve a search query for a Swedish immigration information system. "
        "The current query did not retrieve useful results.\n\n"
        f"Original query: {original_query}{feedback_line}\n\n"
        "Rewrite the query to be more specific and likely to match Swedish immigration content. "
        "Output only the reformulated query, nothing else."
    )

    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["response"].strip()
