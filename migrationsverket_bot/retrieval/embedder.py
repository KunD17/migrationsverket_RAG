"""Embedding logic using Ollama and the chosen local embedding model."""

from __future__ import annotations

from typing import Iterable

import requests

from migrationsverket_bot.config import EMBEDDING_MODEL, OLLAMA_BASE_URL

BATCH_SIZE = 32


class Embedder:
    """Wraps the Ollama embeddings endpoint."""

    def _embed_single(self, text: str) -> list[float]:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embed",
            json={"model": EMBEDDING_MODEL, "input": [text]},
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["embeddings"][0]

    def embed_documents(self, documents: Iterable[str]) -> list[list[float]]:
        """Embed a list of documents in batches, falling back one-at-a-time on error."""
        docs = [d for d in documents if d and d.strip()]
        results: list[list[float]] = []
        for i in range(0, len(docs), BATCH_SIZE):
            batch = docs[i : i + BATCH_SIZE]
            try:
                response = requests.post(
                    f"{OLLAMA_BASE_URL}/api/embed",
                    json={"model": EMBEDDING_MODEL, "input": batch},
                    timeout=120,
                )
                response.raise_for_status()
                results.extend(response.json()["embeddings"])
            except requests.HTTPError:
                # batch rejected — embed one at a time to isolate the bad item
                for text in batch:
                    try:
                        results.append(self._embed_single(text))
                    except Exception:
                        results.append([])
        return results

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string."""
        return self.embed_documents([query])[0]


def embed_documents(documents: Iterable[str]) -> list[list[float]]:
    """Module-level helper: embed a list of documents."""
    return Embedder().embed_documents(documents)


def embed_query(query: str) -> list[float]:
    """Module-level helper: embed a single query."""
    return Embedder().embed_query(query)
