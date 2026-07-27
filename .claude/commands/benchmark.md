# Run the benchmark

```bash
python benchmark.py
```

Runs all 16 questions in `migrationsverket_bot/evaluation/test_set_personal.json`, saves results to `benchmarks/<timestamp>_<commit>.json`, and prints a summary. If a previous run exists, it prints deltas automatically.

## Interpreting results

| Metric | What it means | Target direction |
|---|---|---|
| `pass_rate` | % of questions where all `must_contain` keywords appear and no `must_not_contain` keywords appear | Higher is better |
| `fallback_rate` | % of questions where the agent said "I cannot find" | Moderate — 0% with low pass rate means confidently wrong |
| `avg_confidence` | Mean cosine similarity of retrieved chunks to the query | Higher = retrieval is finding relevant chunks |
| `avg_latency_s` | Mean response time in seconds | Lower is better |

## Reading the per-category breakdown

A 0% category means the agent is either not retrieving relevant chunks for those topics, or the LLM is not grounding its answer in what was retrieved. Low confidence + low pass rate → retrieval problem. High confidence + low pass rate → generation/grounding problem.

## Baseline (2026-06-04, commit 663ae52)

| Metric | Value |
|---|---|
| Pass rate | 31% (5/16) |
| Fallback rate | 0% |
| Avg confidence | 90% |
| Avg latency | 24.6s |
