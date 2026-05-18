"""Scrape Migrationsverket and index content into the vector store."""

import uuid

from migrationsverket_bot.ingestion.scraper import crawl_site
from migrationsverket_bot.ingestion.chunker import chunk_html_by_heading
from migrationsverket_bot.retrieval.embedder import Embedder
from migrationsverket_bot.retrieval.vector_store import VectorStore

MAX_PAGES = 200

print(f"Crawling up to {MAX_PAGES} pages from migrationsverket.se...")
pages = crawl_site(max_pages=MAX_PAGES)
print(f"Crawled {len(pages)} pages.")

store = VectorStore()
embedder = Embedder()

total_chunks = 0
for i, page in enumerate(pages, 1):
    chunks = chunk_html_by_heading(page.get("html", ""))
    if not chunks:
        print(f"  [{i}/{len(pages)}] No chunks — skipping {page['url']}")
        continue

    print(f"  [{i}/{len(pages)}] {len(chunks)} chunks — {page['url']}")
    for chunk in chunks:
        doc_id = str(uuid.uuid4())
        embedding = embedder.embed_query(chunk["text"])
        store.add_documents(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[chunk["text"]],
            metadatas=[{"url": page["url"], "heading": chunk["heading"]}],
        )
        total_chunks += 1

print(f"\nDone. Indexed {total_chunks} chunks from {len(pages)} pages.")