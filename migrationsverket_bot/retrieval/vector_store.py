"""ChromaDB vector store setup, indexing, and retrieval."""

from __future__ import annotations

import chromadb

from migrationsverket_bot.config import TOP_K, DATA_DIR


class VectorStore:
    """Encapsulates ChromaDB storage and search operations."""

    def __init__(self, persist_directory: str | None = None) -> None:
        path = persist_directory or str(DATA_DIR / "chroma")
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(
            name="migrationsverket",
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, str]],
        documents: list[str],
    ) -> None:
        """Insert new documents into the vector store."""
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents,
        )

    def query(self, embedding: list[float], top_k: int = TOP_K) -> list[dict]:
        """Retrieve the top-k nearest documents for a query embedding."""
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, self.collection.count() or 1),
        )
        chunks = []
        for i, doc_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i]
            chunks.append({
                "id": doc_id,
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": distance,
                # cosine distance in chromadb is in [0, 2]; map to [0, 1] confidence
                "confidence": max(0.0, 1.0 - distance / 2.0),
            })
        return chunks

    def persist(self) -> None:
        """No-op: chromadb 0.4+ persists automatically."""
