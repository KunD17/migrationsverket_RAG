"""Handles query and answer translation using the local Ollama LLM."""

from __future__ import annotations

import requests

from migrationsverket_bot.config import OLLAMA_MODEL, OLLAMA_BASE_URL

_LANG_NAMES = {"sv": "Swedish", "en": "English"}


def _ollama_generate(prompt: str) -> str:
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["response"].strip()


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Translate text between Swedish and English using Ollama."""
    src = _LANG_NAMES.get(source_lang, source_lang)
    tgt = _LANG_NAMES.get(target_lang, target_lang)
    prompt = (
        f"Translate the following text from {src} to {tgt}. "
        f"Output only the translation, nothing else.\n\n{text}"
    )
    return _ollama_generate(prompt)


def translate_query(query: str, detected_lang: str) -> tuple[str, bool]:
    """Translate a non-Swedish query to Swedish before retrieval."""
    if detected_lang != "sv":
        return translate_text(query, source_lang=detected_lang, target_lang="sv"), True
    return query, False


def translate_response(answer: str, target_lang: str) -> tuple[str, bool]:
    """Translate the Swedish answer into the user's language if it isn't Swedish."""
    if target_lang != "sv":
        return translate_text(answer, source_lang="sv", target_lang=target_lang), True
    return answer, False
