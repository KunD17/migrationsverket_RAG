"""Detects the language of the incoming user query."""

from __future__ import annotations

from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0


def detect_language(text: str) -> str:
    """Return the detected ISO language code for a query."""
    return detect(text)
