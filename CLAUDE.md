# Migrationsverket RAG — Claude Code Brief

Local RAG chatbot for Swedish immigration questions. No API keys — everything runs via Ollama (`llama3.1` + `nomic-embed-text`).

For module-level detail see [ARCHITECTURE.md](ARCHITECTURE.md).

## Key Commands

```bash
python run_tests.py                          # fast feedback — no saved output
python benchmark.py                          # saves result + prints delta vs previous run
python -m streamlit run migrationsverket_bot/ui/app.py
python ingest_personal.py                    # incremental re-ingest
```

## Config Knobs (`migrationsverket_bot/config.py`)

| Setting | Default | Effect |
|---|---|---|
| `OLLAMA_MODEL` | `llama3.1` | LLM for generation, reformulation, translation |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model |
| `TOP_K` | `5` | Chunks retrieved per query |
| `CONFIDENCE_THRESHOLD` | `0.4` | Cosine similarity cutoff for fallback |
| `RETRY_LIMIT` | `2` | Reformulation attempts before fallback |

## Performance Baseline (2026-06-04)

- Pass rate: **31% (5/16)** — this is what we are improving
- Fallback rate: 0% — the agent is confidently wrong, not falling back
- Avg confidence: 90% — retrieval is finding relevant chunks
- Avg latency: 24.6s

**Known bottleneck:** high retrieval confidence + low pass rate = the LLM is not grounding its answers in the retrieved chunks. Generation/prompting problem, not a retrieval problem.

Failing categories: `researcher` (0%), `eu_blue_card` (0%), `family_reunification` (0%), `work_permit` (25%).

## Iteration Loop

1. Change something (prompt, config, retrieval logic)
2. `python run_tests.py` — fast check, no saved record
3. If promising → `python benchmark.py` — saves a comparable record with deltas

## Do Not

- Merge `translator.py`, `language_detector.py`, or `relevance_checker.py` into `rag_agent.py`
- Use fixed character-size chunking — chunk by heading structure
- Skip the relevance check step
- Hardcode parameters that belong in `config.py`
- Use any external API — everything via Ollama
