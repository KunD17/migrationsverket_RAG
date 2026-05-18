"""Streamlit UI for the Migrationsverket RAG chatbot."""

from __future__ import annotations

import json
import sqlite3

import pandas as pd
import streamlit as st

from migrationsverket_bot.agent.rag_agent import RAGAgent
from migrationsverket_bot.config import LOGGING_DB, PROJECT_NAME
from migrationsverket_bot.observability.logger import log_query_to_db
from migrationsverket_bot.retrieval.embedder import Embedder
from migrationsverket_bot.retrieval.vector_store import VectorStore

_LANG_MAP = {"Auto": None, "Svenska": "sv", "English": "en"}


@st.cache_resource(show_spinner="Loading vector store…")
def _get_agent() -> RAGAgent:
    return RAGAgent(
        vector_store=VectorStore(),
        embedder=Embedder(),
        logger=log_query_to_db,
    )


def _render_chat(agent: RAGAgent, lang_override: str | None) -> None:
    st.header("Chat")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("Källor / Sources"):
                    for src in msg["sources"]:
                        label = src.get("section") or src.get("url") or "Link"
                        url = src.get("url", "#")
                        st.markdown(f"- [{label}]({url})")
            if msg["role"] == "assistant":
                badges = []
                if msg.get("confidence") is not None:
                    badges.append(f"Confidence: {msg['confidence']:.0%}")
                if msg.get("translated"):
                    badges.append("Translated")
                if msg.get("latency") is not None:
                    badges.append(f"{msg['latency']:.1f}s")
                if badges:
                    st.caption(" · ".join(badges))

    if user_input := st.chat_input("Ställ en fråga om svensk immigration…"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Söker och genererar svar…"):
                result = agent.answer(user_input, explicit_language=lang_override)
            st.markdown(result["answer"])
            if result["sources"]:
                with st.expander("Källor / Sources"):
                    for src in result["sources"]:
                        label = src.get("section") or src.get("url") or "Link"
                        url = src.get("url", "#")
                        st.markdown(f"- [{label}]({url})")
            badges = [f"Confidence: {result['confidence']:.0%}"]
            if result["translated"]:
                badges.append("Translated")
            badges.append(f"{result['latency']:.1f}s")
            st.caption(" · ".join(badges))

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "confidence": result["confidence"],
            "translated": result["translated"],
            "latency": result["latency"],
        })


def _render_metrics() -> None:
    st.header("Metrics Dashboard")

    try:
        with sqlite3.connect(LOGGING_DB) as conn:
            df = pd.read_sql_query(
                "SELECT * FROM query_log ORDER BY timestamp DESC", conn
            )
    except Exception:
        st.info("No query log yet — send some queries in the Chat tab first.")
        return

    if df.empty:
        st.info("No queries logged yet.")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Queries", len(df))
    col2.metric(
        "Avg Latency",
        f"{df['latency'].mean():.1f}s" if "latency" in df.columns else "—",
    )
    col3.metric(
        "Translation Rate",
        f"{df['query_translated'].mean():.0%}" if "query_translated" in df.columns else "—",
    )
    col4.metric(
        "Avg Confidence",
        f"{df['confidence'].mean():.0%}" if "confidence" in df.columns else "—",
    )

    st.subheader("Query Log")
    display_cols = [c for c in
        ["timestamp", "query", "detected_language", "confidence", "query_translated", "latency"]
        if c in df.columns]
    st.dataframe(df[display_cols], use_container_width=True)

    if "sources" in df.columns:
        st.subheader("Recent Sources")
        for raw in df["sources"].dropna().head(10):
            try:
                for src in json.loads(raw):
                    url = src.get("url", "")
                    if url:
                        st.markdown(f"- {url}")
            except (json.JSONDecodeError, TypeError):
                pass


def main() -> None:
    """Run the Streamlit application."""
    st.set_page_config(page_title=PROJECT_NAME, page_icon="🧭", layout="wide")
    st.sidebar.title(PROJECT_NAME)

    tab = st.sidebar.radio("Navigate / Navigera:", ["Chat", "Metrics"])
    lang_label = st.sidebar.selectbox(
        "Language / Språk",
        ["Auto", "Svenska", "English"],
        help="Override automatic language detection.",
    )
    lang_override = _LANG_MAP[lang_label]

    agent = _get_agent()

    if tab == "Chat":
        _render_chat(agent, lang_override)
    else:
        _render_metrics()


if __name__ == "__main__":
    main()
