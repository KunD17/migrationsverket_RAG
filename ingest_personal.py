"""
Ingest Migrationsverket pages relevant to:
  - A researcher/student who moved to Sweden and is now working
  - Inviting friends and family to visit

Drives ingestion from the sitemap — no crawling guesswork.
Re-run anytime — already-ingested URLs are skipped automatically.
"""

import gzip
import re
import uuid

import requests
from bs4 import BeautifulSoup

from migrationsverket_bot.config import USER_AGENT
from migrationsverket_bot.ingestion.chunker import chunk_html_by_heading
from migrationsverket_bot.ingestion.scraper import fetch_url
from migrationsverket_bot.ingestion.tracker import load, mark_ingested
from migrationsverket_bot.retrieval.embedder import Embedder
from migrationsverket_bot.retrieval.vector_store import VectorStore

HEADERS = {"User-Agent": USER_AGENT}
SITEMAP_URL = "https://www.migrationsverket.se/sitemap1.xml.gz"

RELEVANT_KEYWORDS = [
    "work", "arbeta", "arbetstillstand", "work-permit",
    "highly-qualified", "hogkvalificerad",
    "eu-blue-card", "blue-card",
    "researcher", "forskar",
    "self-employ", "eget-foretag",
    "intracompany", "ict-permit",
    "specialist",
    "studi", "study", "student",
    "jobseeker", "jobbsokare",
    "extend", "forlanga", "renew",
    "change-condition", "andra-villkor",
    "permanent",
    "citizenship", "medborgarskap",
    "family-reunif", "familjeaterforening",
    "visit", "besoka", "besok",
    "invite", "bjuda",
    "schengen", "visering",
]

SKIP_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf", ".gz", ".zip"}


def is_relevant(url: str) -> bool:
    return any(kw in url.lower() for kw in RELEVANT_KEYWORDS)


def is_content_page(url: str) -> bool:
    return not any(url.lower().endswith(ext) for ext in SKIP_EXTENSIONS)


# ------------------------------------------------------------------
# 1. Pull URLs from sitemap
# ------------------------------------------------------------------
print("Fetching sitemap...")
response = requests.get(SITEMAP_URL, headers=HEADERS, timeout=30)
response.raise_for_status()
xml = gzip.decompress(response.content).decode("utf-8")
all_urls = re.findall(r"<loc>(https://[^<]+)</loc>", xml)
print(f"  Total URLs in sitemap: {len(all_urls)}")

relevant_urls = [u for u in all_urls if is_relevant(u) and is_content_page(u)]
print(f"  Relevant content pages: {len(relevant_urls)}")

# ------------------------------------------------------------------
# 2. Skip already-ingested URLs
# ------------------------------------------------------------------
log = load()
new_urls = [u for u in relevant_urls if u not in log]
print(f"  Already ingested:       {len(relevant_urls) - len(new_urls)}")
print(f"  To ingest now:          {len(new_urls)}\n")

if not new_urls:
    print("Nothing new to ingest. Run again after the website updates.")
    raise SystemExit(0)

# ------------------------------------------------------------------
# 3. Fetch, chunk, embed, store
# ------------------------------------------------------------------
store = VectorStore()
embedder = Embedder()

total_chunks = 0
for i, url in enumerate(new_urls, 1):
    try:
        html = fetch_url(url)
    except Exception as e:
        print(f"  [{i}/{len(new_urls)}] FAILED to fetch — {url} ({e})")
        mark_ingested([url], log)
        continue

    soup = BeautifulSoup(html, "html.parser")
    article = soup.find("article") or soup.find("main") or soup
    chunks = chunk_html_by_heading(str(article))
    if not chunks:
        print(f"  [{i}/{len(new_urls)}] No chunks — skipping {url}")
        mark_ingested([url], log)
        continue

    print(f"  [{i}/{len(new_urls)}] {len(chunks)} chunks — {url}")
    texts = [c["text"] for c in chunks]
    embeddings = embedder.embed_documents(texts)

    valid = [(t, e, c) for t, e, c in zip(texts, embeddings, chunks) if e]
    if not valid:
        mark_ingested([url], log)
        continue
    v_texts, v_embeddings, v_chunks = zip(*valid)

    store.add_documents(
        ids=[str(uuid.uuid4()) for _ in v_chunks],
        embeddings=list(v_embeddings),
        documents=list(v_texts),
        metadatas=[{"url": url, "heading": c["heading"]} for c in v_chunks],
    )
    mark_ingested([url], log)
    total_chunks += len(chunks)

print(f"\nDone. Indexed {total_chunks} new chunks from {len(new_urls)} pages.")
print(f"Tracker now covers {len(log)} URLs total.")