# Architecture Reference

Detailed breakdown of every module in the project. For running and configuring the bot, see [README.md](README.md). For Claude Code session context, see [CLAUDE.md](CLAUDE.md).

## Module Map

### `ingestion/`

| File | What it does |
|---|---|
| `scraper.py` | Fetches pages from migrationsverket.se using `requests` + `BeautifulSoup`. Extracts main content HTML, strips nav/footer/cookie banners, and returns structured page data (URL, title, body text). Respects `SCRAPE_TIMEOUT` from config. |
| `chunker.py` | Splits page content by heading structure (`<h2>`, `<h3>`) — not fixed character size. Each chunk carries its source URL and section heading as metadata, which becomes the citation shown in the UI. |
| `tracker.py` | Reads/writes `migrationsverket_bot/data/ingested_urls.json`. On each ingestion run, already-seen URLs are skipped so re-runs only pick up new pages. |

### `retrieval/`

| File | What it does |
|---|---|
| `embedder.py` | Sends text to Ollama's `/api/embed` endpoint using `nomic-embed-text`. Batched to avoid overwhelming Ollama. Returns numpy arrays for cosine similarity scoring. |
| `vector_store.py` | Wraps ChromaDB. Handles collection creation, upserting chunks with metadata, and querying top-k results. Persists to `migrationsverket_bot/data/chroma`. |

### `agent/`

| File | What it does |
|---|---|
| `language_detector.py` | Uses `langdetect` to identify whether the query is Swedish (`sv`) or English (`en`). Returns a language code used by the translator and logger. |
| `translator.py` | Translates between Swedish and English via the local Ollama LLM. Used in two places: query→Swedish before retrieval, and answer→English before display if the user's language is English. |
| `relevance_checker.py` | Scores retrieval results using cosine similarity — no LLM call. If the top chunk score is below `CONFIDENCE_THRESHOLD` (default 0.4), signals the agent to reformulate. |
| `query_reformulator.py` | Uses the LLM to rephrase a low-confidence query. Called up to `RETRY_LIMIT` (default 2) times before the agent falls back. |
| `rag_agent.py` | Orchestrates the full pipeline. The loop in order: detect language → translate query → embed → retrieve → relevance check → (reformulate if needed) → generate answer → translate answer → log. Returns a dict with `answer`, `confidence`, `latency`, and `sources`. |

### `evaluation/`

| File | What it does |
|---|---|
| `test_set_personal.json` | 16 manually written questions covering the researcher use case. Each question has `must_contain` (keywords that must appear in the answer) and `must_not_contain` (keywords that must not). Used by both `run_tests.py` and `benchmark.py`. |
| `test_set.json` | Broader test set. Not used in the current benchmark run. |
| `evaluator.py` | Evaluation logic — checks answers against keyword lists and computes pass/fail. |
| `metrics_logger.py` | Logs evaluation results to SQLite. |

### `observability/`

| File | What it does |
|---|---|
| `logger.py` | Logs every agent interaction to SQLite (`migrationsverket_rag.sqlite`). Records: original query, detected language, reformulated query (if any), chunks retrieved, confidence scores, whether translation was applied, final answer, and latency. |

### `ui/`

| File | What it does |
|---|---|
| `app.py` | Streamlit app with two tabs. **Chat tab:** language toggle (overrides auto-detection), answer display with source citations and confidence indicator. **Metrics tab:** query history table, average latency, confidence distribution. |

### Root-level scripts

| File | What it does |
|---|---|
| `ingest_personal.py` | Pulls the full sitemap, filters to ~1100 relevant pages (work permits, researchers, visiting, permanent residency, citizenship), and indexes them incrementally. |
| `ingest.py` | Unfiltered ingestion — indexes all ~4000 pages on the site. Slower and noisier. |
| `run_tests.py` | Runs the 16-question test set and prints PASS/FAIL per question. No saved output — use for quick feedback during development. |
| `benchmark.py` | Same as `run_tests.py` but saves results to `benchmarks/<timestamp>_<commit>.json` and prints deltas vs the previous run. Use this when you want a comparable record. |
| `assess_extent_of_website.py` | One-off script that analyses the sitemap to understand how many pages exist and what topics they cover. |
| `config.py` | Single source of truth for all parameters. Nothing is hardcoded in other modules. |

## Agent Loop (in order — do not collapse or reorder)

```
1. Receive query
2. Detect language (language_detector.py)
3. If English → translate query to Swedish (translator.py)
4. Embed query (embedder.py)
5. Retrieve top-k chunks from ChromaDB (vector_store.py)
6. Score relevance (relevance_checker.py — cosine similarity, no LLM)
7. If score < CONFIDENCE_THRESHOLD:
     a. Reformulate query (query_reformulator.py)
     b. Re-embed and re-retrieve
     c. Repeat up to RETRY_LIMIT times
8. If still below threshold → return fallback response in user's language
9. Generate answer grounded in retrieved chunks (rag_agent.py → Ollama)
10. If user language is English → translate answer (translator.py)
11. Log full interaction (logger.py)
12. Return answer + confidence + latency + sources
```

## Data Flow Diagram

```
Query (EN or SV)
    │
    ▼
language_detector.py ──► detected_lang
    │
    ▼ (if EN)
translator.py ──► Swedish query
    │
    ▼
embedder.py ──► query vector
    │
    ▼
vector_store.py ──► top-k chunks + scores
    │
    ▼
relevance_checker.py
    │
    ├─ LOW ──► query_reformulator.py ──► (loop back, max RETRY_LIMIT)
    │
    └─ HIGH ──► Ollama (llama3.1) ──► Swedish answer
                    │
                    ▼ (if EN)
                translator.py ──► English answer
                    │
                    ▼
                logger.py ──► SQLite
                    │
                    ▼
                UI / caller
```
