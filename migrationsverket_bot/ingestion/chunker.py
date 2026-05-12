"""Document chunking for section-based RAG ingestion."""

from __future__ import annotations

from bs4 import BeautifulSoup


def chunk_html_by_heading(html: str) -> list[dict[str, str]]:
    """Split HTML content into chunks by heading structure rather than fixed character size."""
    soup = BeautifulSoup(html, "html.parser")
    chunks: list[dict[str, str]] = []
    current_section: dict[str, str] = {"heading": "Introduction", "text": ""}

    for element in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li"]):
        if element.name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            if current_section["text"]:
                chunks.append(current_section)
            current_section = {"heading": element.get_text(strip=True), "text": ""}
        else:
            text = element.get_text(strip=True)
            if text:
                current_section["text"] += text + "\n"

    if current_section["text"]:
        chunks.append(current_section)

    return chunks


def chunk_text_by_section(title: str, body: str) -> list[dict[str, str]]:
    """Create chunk metadata for extracted Swedish content."""
    return [{"heading": title, "text": body}] if body else []
