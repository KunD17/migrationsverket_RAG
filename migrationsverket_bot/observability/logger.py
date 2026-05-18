"""Application observability: structured logging to stdout and SQLite."""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Any

from migrationsverket_bot.config import LOGGING_DB

_logger = logging.getLogger("migrationsverket_bot")
if not _logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    _logger.addHandler(_handler)
_logger.setLevel(logging.INFO)


def log_info(message: str, **metadata: object) -> None:
    """Log an informational event with optional metadata."""
    _logger.info("%s | %s", message, metadata)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS query_log (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp               TEXT,
    query                   TEXT,
    detected_language       TEXT,
    target_language         TEXT,
    query_translated        INTEGER,
    reformulated_query      TEXT,
    chunks_retrieved        INTEGER,
    relevance_decision      INTEGER,
    confidence              REAL,
    translation_steps       TEXT,
    answer                  TEXT,
    sources                 TEXT,
    latency                 REAL
)
"""


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(_SCHEMA)
    conn.commit()


def log_query_to_db(record: dict[str, Any]) -> None:
    """Persist a full query interaction to the SQLite query log."""
    translation_steps = json.dumps({
        "query_translated": record.get("query_translated", False),
        "answer_translated": record.get("translated", False),
    })
    with sqlite3.connect(LOGGING_DB) as conn:
        _ensure_schema(conn)
        conn.execute(
            """
            INSERT INTO query_log (
                timestamp, query, detected_language, target_language,
                query_translated, reformulated_query, chunks_retrieved,
                relevance_decision, confidence, translation_steps,
                answer, sources, latency
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                record.get("query"),
                record.get("detected_language"),
                record.get("target_language"),
                int(record.get("query_translated", False)),
                record.get("reformulated_query"),
                record.get("chunks_retrieved", 0),
                int(record.get("relevance_decision", False)),
                record.get("confidence"),
                translation_steps,
                record.get("answer"),
                json.dumps(record.get("sources", [])),
                record.get("latency"),
            ),
        )
