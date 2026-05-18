"""Embedding logic using Ollama and the chosen local embedding model."""

from __future__ import annotations

from typing import Iterable

import requests

from migrationsverket_bot.config import EMBEDDING_MODEL, OLLAMA_BASE_URL


class Embedder:
    """Wraps the Ollama embeddings endpoint."""

    def embed_documents(self, documents: Iterable[str]) -> list[list[float]]:
        """Embed a list of documents with the local embedding model."""
        return [self.embed_query(doc) for doc in documents]

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string."""
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": EMBEDDING_MODEL, "prompt": query},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["embedding"]


def embed_documents(documents: Iterable[str]) -> list[list[float]]:
    """Module-level helper: embed a list of documents."""
    return Embedder().embed_documents(documents)


def embed_query(query: str) -> list[float]:
    """Module-level helper: embed a single query."""
    return Embedder().embed_query(query)
