"""Logs evaluation results and query interactions to SQLite."""

from __future__ import annotations

import sqlite3

from migrationsverket_bot.config import LOGGING_DB


def initialize_db() -> None:
    """Create the logging database schema if it does not exist."""
    with sqlite3.connect(LOGGING_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS query_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                query TEXT,
                detected_language TEXT,
                target_language TEXT,
                translated BOOLEAN,
                relevance REAL,
                confidence REAL,
                answer TEXT,
                sources TEXT,
                latency REAL
            )
            """
        )
        conn.commit()


def log_query(record: dict[str, object]) -> None:
    """Insert a query interaction into the SQLite log."""
    with sqlite3.connect(LOGGING_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO query_log (
                timestamp, query, detected_language, target_language,
                translated, relevance, confidence, answer, sources, latency
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.get("timestamp"),
                record.get("query"),
                record.get("detected_language"),
                record.get("target_language"),
                int(record.get("translated", False)),
                record.get("relevance"),
                record.get("confidence"),
                record.get("answer"),
                record.get("sources"),
                record.get("latency"),
            ),
        )
        conn.commit()
