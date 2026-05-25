"""Tracks which URLs have already been ingested to avoid duplicates on re-runs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from migrationsverket_bot.config import DATA_DIR

TRACKER_PATH = DATA_DIR / "ingested_urls.json"


def load() -> dict[str, str]:
    """Return {url: iso_timestamp} for all previously ingested URLs."""
    if not TRACKER_PATH.exists():
        return {}
    with open(TRACKER_PATH) as f:
        return json.load(f)


def save(log: dict[str, str]) -> None:
    TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACKER_PATH, "w") as f:
        json.dump(log, f, indent=2)


def mark_ingested(urls: list[str], log: dict[str, str]) -> None:
    """Add URLs to the log with the current timestamp and save."""
    now = datetime.now(timezone.utc).isoformat()
    for url in urls:
        log[url] = now
    save(log)


def filter_new(pages: list[dict], log: dict[str, str]) -> list[dict]:
    """Return only pages whose URL is not already in the log."""
    return [p for p in pages if p["url"] not in log]