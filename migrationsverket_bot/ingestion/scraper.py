"""Scraper module for Migrationsverket website content."""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from migrationsverket_bot.config import BASE_URL, USER_AGENT, SCRAPE_TIMEOUT

HEADERS = {"User-Agent": USER_AGENT}


def fetch_url(url: str) -> str:
    """Download raw HTML for a given URL."""
    response = requests.get(url, headers=HEADERS, timeout=SCRAPE_TIMEOUT)
    response.raise_for_status()
    return response.text


def scrape_page(url: str) -> dict[str, str]:
    """Scrape a page and return title, plain-text body, and raw html."""
    html = fetch_url(url)
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.get_text(strip=True) if soup.title else url
    article = soup.find("article") or soup.find("main") or soup
    body = article.get_text(separator="\n", strip=True)

    return {"url": url, "title": title, "body": body, "html": html}


def _is_migrationsverket_url(url: str) -> bool:
    parsed = urlparse(url)
    base_parsed = urlparse(BASE_URL)
    return parsed.netloc == base_parsed.netloc


def discover_links(html: str, base_url: str) -> list[str]:
    """Extract all internal Swedish-language links from a page."""
    soup = BeautifulSoup(html, "html.parser")
    links: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        full_url = urljoin(base_url, anchor["href"]).split("#")[0]
        if _is_migrationsverket_url(full_url) and "/en/" not in urlparse(full_url).path:
            links.add(full_url)
    return list(links)


def crawl_site(start_url: str = BASE_URL, max_pages: int = 100) -> list[dict[str, str]]:
    """Crawl Migrationsverket from start_url and return scraped pages (without raw html)."""
    visited: set[str] = set()
    queue: list[str] = [start_url]
    pages: list[dict[str, str]] = []

    while queue and len(visited) < max_pages:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        try:
            page = scrape_page(url)
            new_links = discover_links(page["html"], url)
            queue.extend(link for link in new_links if link not in visited)
            page.pop("html")
            pages.append(page)
        except Exception:
            continue

    return pages
