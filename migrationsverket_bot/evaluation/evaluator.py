"""Evaluation module for measuring retrieval and answer quality."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import requests

from migrationsverket_bot.config import EVALUATION_TEST_SET_PATH, OLLAMA_MODEL, OLLAMA_BASE_URL

if TYPE_CHECKING:
    from migrationsverket_bot.agent.rag_agent import RAGAgent


def load_test_set() -> list[dict[str, str]]:
    """Load the evaluation test set from JSON."""
    with open(EVALUATION_TEST_SET_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _llm_score(prompt: str) -> float:
    """Call Ollama and parse a 0–1 score from its response."""
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=60,
    )
    response.raise_for_status()
    text = response.json()["response"].strip()
    try:
        return min(max(float(text.split()[0].rstrip(".,)")), 0.0), 1.0)
    except (ValueError, IndexError):
        return 0.5


def _faithfulness_score(question: str, context: str, answer: str) -> float:
    """Use the LLM to score how faithfully the answer is grounded in context."""
    prompt = (
        "Does the following answer faithfully represent the information in the context "
        "without hallucination?\n\n"
        f"Context: {context}\nQuestion: {question}\nAnswer: {answer}\n\n"
        "Reply with only a single number from 0.0 (hallucinated) to 1.0 (fully grounded)."
    )
    return _llm_score(prompt)


def _translation_quality_score(original_sv: str, translated_en: str) -> float:
    """Use the LLM to score whether the English translation preserves the Swedish meaning."""
    prompt = (
        "Does the English translation accurately preserve the meaning of the Swedish source?\n\n"
        f"Swedish: {original_sv}\nEnglish: {translated_en}\n\n"
        "Reply with only a single number from 0.0 (meaning lost) to 1.0 (perfect)."
    )
    return _llm_score(prompt)


def evaluate(agent: "RAGAgent | None" = None) -> dict[str, float]:
    """Run evaluation on the test set and return summary metrics."""
    if agent is None:
        return {"retrieval_accuracy": 0.0, "faithfulness": 0.0, "translation_quality": 0.0}

    test_cases = load_test_set()
    retrieval_hits = 0
    faithfulness_scores: list[float] = []
    translation_scores: list[float] = []

    for case in test_cases:
        result = agent.answer(case["question"])

        # Retrieval accuracy: did we retrieve anything at all?
        if result["chunks_retrieved"] > 0:
            retrieval_hits += 1

        # Faithfulness: is the answer grounded in retrieved text?
        if result["chunks_retrieved"] > 0:
            context = " ".join(s.get("section", "") for s in result.get("sources", []))
            score = _faithfulness_score(case["question"], context, result["answer"])
            faithfulness_scores.append(score)

        # Translation quality: for English questions, compare Swedish source to English answer
        if case.get("language") == "en" and result.get("translated"):
            sv_result = agent.answer(case["question"], explicit_language="sv")
            t_score = _translation_quality_score(sv_result["answer"], result["answer"])
            translation_scores.append(t_score)

    n = len(test_cases)
    return {
        "retrieval_accuracy": retrieval_hits / n if n else 0.0,
        "faithfulness": (
            sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else 0.0
        ),
        "translation_quality": (
            sum(translation_scores) / len(translation_scores) if translation_scores else 0.0
        ),
    }
