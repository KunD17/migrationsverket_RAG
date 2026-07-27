# Run ingestion

## Incremental (normal)

Only fetches URLs not already in `migrationsverket_bot/data/ingested_urls.json`:

```bash
python ingest_personal.py
```

## Full re-ingest from scratch

Wipes the Chroma store and the URL tracker, then re-indexes everything (~1100 pages):

```bash
rm -rf migrationsverket_bot/data/chroma
rm -f migrationsverket_bot/data/ingested_urls.json
python ingest_personal.py
```

This takes a while — the scraper respects `SCRAPE_TIMEOUT = 30s` per page and the embedder batches via Ollama.

## What gets indexed

`ingest_personal.py` pulls the full sitemap from migrationsverket.se and filters to ~1100 pages covering: work permits, researchers, studying, visiting, permanent residency, and citizenship. Generic/admin pages are excluded.

`ingest.py` is the unfiltered version — indexes all ~4000 pages.
