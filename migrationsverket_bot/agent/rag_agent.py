"""Main retrieval-augmented generation (RAG) agent combining the full pipeline."""

from __future__ import annotations

import re
import time
from typing import Any, Callable

import requests

from migrationsverket_bot.agent.language_detector import detect_language
from migrationsverket_bot.agent.query_reformulator import reformulate_query
from migrationsverket_bot.agent.relevance_checker import assess_relevance
from migrationsverket_bot.agent.translator import translate_query, translate_response
from migrationsverket_bot.config import (
    CONFIDENCE_THRESHOLD,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TEMPERATURE,
    RETRY_LIMIT,
)

_NUMERIC_FACT_PATTERN = re.compile(r"\b\d[\d.,]*%?\b")


def _numeric_facts(text: str) -> set[str]:
    """Pull out numbers, percentages, and form-like codes for verbatim grounding checks."""
    return set(_NUMERIC_FACT_PATTERN.findall(text))


def _call_ollama(prompt: str) -> str:
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": OLLAMA_TEMPERATURE},
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["response"].strip()

_FALLBACK = {
    "sv": (
        "Tyvärr kan jag inte hitta ett svar på din fråga i Migrationsverkets data. "
        "Besök gärna Migrationsverkets webbplats direkt: https://www.migrationsverket.se"
    ),
    "en": (
        "I was unable to find an answer to your question in the Migrationsverket data. "
        "Please visit the website directly: https://www.migrationsverket.se"
    ),
}


def _generate_answer(query: str, chunks: list[dict]) -> str:
    """Generate a grounded Swedish answer from retrieved chunks."""
    context_parts = []
    for c in chunks:
        meta = c.get("metadata") or {}
        url = meta.get("url", "okänd källa")
        section = meta.get("heading", "")
        text = c.get("document", "")
        context_parts.append(f"[Källa: {url} | Avsnitt: {section}]\n{text}")
    context = "\n\n".join(context_parts)

    prompt = (
        "You are a helpful assistant answering questions about Swedish immigration "
        "based strictly on the provided context below. "
        "Answer in the same language as the question. "
        "Be specific and practical — list steps, documents, and requirements where relevant. "
        "First identify every specific number, date, percentage, deadline, and form/document "
        "name in the context that is relevant to the question, then include all of them "
        "verbatim in your answer — do not paraphrase, round, or omit them. "
        "IMPORTANT: never state that something is NOT required or NOT necessary unless "
        "the context explicitly says so. If you are unsure, omit the statement entirely. "
        "Only say you don't know if the context genuinely contains no relevant information.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer:"
    )

    answer = _call_ollama(prompt)

    missing_facts = _numeric_facts(context) - _numeric_facts(answer)
    if missing_facts:
        correction_prompt = (
            f"{prompt}{answer}\n\n"
            "The context contains these specific values that your answer above did not "
            f"mention: {', '.join(sorted(missing_facts))}. If any of them are relevant to "
            "the question, revise your answer to include them verbatim. Otherwise repeat "
            "your answer unchanged.\n\n"
            "Revised answer:"
        )
        answer = _call_ollama(correction_prompt)

    return answer


class RAGAgent:
    """Encapsulates the full multilingual RAG pipeline."""

    def __init__(
        self,
        vector_store: Any,
        embedder: Any,
        logger: Callable[[dict], None] | None = None,
    ) -> None:
        self.vector_store = vector_store
        self.embedder = embedder
        self.logger = logger

    def answer(self, query: str, explicit_language: str | None = None) -> dict[str, Any]:
        """Run the end-to-end query pipeline and return a structured response."""
        start = time.time()

        detected_language = detect_language(query)
        target_language = explicit_language or detected_language

        _, query_translated = translate_query(query, detected_language)

        current_query = query
        reformulated_query: str | None = None
        chunks: list[dict] = []
        relevance_score = 0.0

        for attempt in range(RETRY_LIMIT + 1):
            embedding = self.embedder.embed_query(current_query)
            raw_chunks = self.vector_store.query(embedding)
            chunks = [c for c in raw_chunks if len(c.get("document") or "") > 100]
            relevance_score = assess_relevance(current_query, chunks)

            if relevance_score >= CONFIDENCE_THRESHOLD:
                break

            if attempt < RETRY_LIMIT:
                reformulated_query = reformulate_query(
                    current_query,
                    feedback=f"relevance score was {relevance_score:.2f}",
                )
                current_query = reformulated_query

        relevant = relevance_score >= CONFIDENCE_THRESHOLD and chunks
        if relevant:
            answer_sv = _generate_answer(current_query, chunks)
            answer, answer_translated = translate_response(answer_sv, target_language)
            sources = [
                {
                    "url": (c.get("metadata") or {}).get("url", ""),
                    "section": (c.get("metadata") or {}).get("heading", ""),
                }
                for c in chunks
            ]
        else:
            answer = _FALLBACK.get(target_language, _FALLBACK["en"])
            answer_translated = False
            sources = []

        result: dict[str, Any] = {
            "query": query,
            "detected_language": detected_language,
            "target_language": target_language,
            "query_translated": query_translated,
            "reformulated_query": reformulated_query,
            "chunks_retrieved": len(chunks),
            "relevance_decision": bool(relevant),
            "confidence": relevance_score,
            "answer": answer,
            "translated": answer_translated,
            "sources": sources,
            "latency": time.time() - start,
        }

        if self.logger:
            self.logger(result)

        return result
