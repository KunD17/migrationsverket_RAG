"""
Performance evaluation of the RAGAgent on a fixed set of questions with known expected keywords in the answers.

Metrics (objective — no LLM scoring):
  pass_rate      % of questions where must_contain keywords appear and
                 must_not_contain keywords are absent
  fallback_rate  % of questions that hit the "I cannot find" fallback
  avg_confidence mean cosine similarity score across all questions
  avg_latency_s  mean response time in seconds
  per_category   pass_rate broken down by category
"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from migrationsverket_bot.agent.rag_agent import RAGAgent
from migrationsverket_bot.retrieval.embedder import Embedder
from migrationsverket_bot.retrieval.vector_store import VectorStore

TEST_SET = Path("migrationsverket_bot/evaluation/test_set_personal.json")
BENCHMARKS_DIR = Path("benchmarks")
BENCHMARKS_DIR.mkdir(exist_ok=True)

FALLBACK_PHRASES = ["i was unable", "i cannot", "i am unable", "cannot find an answer"]


def _git(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:
        return "unknown"


def load_previous() -> dict | None:
    runs = sorted(BENCHMARKS_DIR.glob("*.json"))
    if len(runs) < 2:
        return None
    with open(runs[-2]) as f:
        return json.load(f)


def fmt_delta(current: float, previous: float, higher_is_better: bool = True) -> str:
    d = current - previous
    if higher_is_better:
        symbol = "▲" if d > 0 else ("▼" if d < 0 else "–")
    else:
        symbol = "▼" if d > 0 else ("▲" if d < 0 else "–")
    sign = "+" if d >= 0 else ""
    return f"{sign}{d:.1%} {symbol}"


# ------------------------------------------------------------------

with open(TEST_SET) as f:
    tests = json.load(f)

commit = _git(["git", "rev-parse", "--short", "HEAD"])
branch = _git(["git", "rev-parse", "--abbrev-ref", "HEAD"])

print(f"Benchmarking  commit={commit}  branch={branch}")
print(f"Running {len(tests)} questions...\n")

agent = RAGAgent(vector_store=VectorStore(), embedder=Embedder())

results = []
category_results: dict[str, list[bool]] = {}

for test in tests:
    qid = test["id"]
    category = test.get("category", "other")
    question = test["question"]
    must_contain = [kw.lower() for kw in test.get("must_contain", [])]
    must_not_contain = [kw.lower() for kw in test.get("must_not_contain", [])]

    print(f"  [{qid}] {question[:72]}...")
    result = agent.answer(question)
    answer_lower = result["answer"].lower()

    missing = [kw for kw in must_contain if kw not in answer_lower]
    forbidden = [kw for kw in must_not_contain if kw in answer_lower]
    passed = not missing and not forbidden
    fallback = any(p in answer_lower for p in FALLBACK_PHRASES)

    label = "PASS" if passed else "FAIL"
    print(f"    {label}  confidence={result['confidence']:.0%}  {result['latency']:.1f}s")
    if missing:
        print(f"    missing keywords : {missing}")
    if forbidden:
        print(f"    forbidden found  : {forbidden}")

    results.append({
        "id": qid,
        "category": category,
        "passed": passed,
        "fallback": fallback,
        "confidence": result["confidence"],
        "latency": result["latency"],
        "missing_keywords": missing,
        "forbidden_found": forbidden,
        "answer": result["answer"],
    })
    category_results.setdefault(category, []).append(passed)

# ------------------------------------------------------------------

n = len(results)
metrics = {
    "pass_rate": sum(r["passed"] for r in results) / n,
    "fallback_rate": sum(r["fallback"] for r in results) / n,
    "avg_confidence": sum(r["confidence"] for r in results) / n,
    "avg_latency_s": sum(r["latency"] for r in results) / n,
    "per_category": {cat: sum(v) / len(v) for cat, v in category_results.items()},
}

run = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "commit": commit,
    "branch": branch,
    "metrics": metrics,
    "results": results,
}

ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
out_path = BENCHMARKS_DIR / f"{ts}_{commit}.json"
with open(out_path, "w") as f:
    json.dump(run, f, indent=2)

# ------------------------------------------------------------------

w = 55
print(f"\n{'='*w}")
print(f"  commit      {commit}  ({branch})")
print(f"  pass rate   {metrics['pass_rate']:.0%}  ({sum(r['passed'] for r in results)}/{n})")
print(f"  fallback    {metrics['fallback_rate']:.0%}")
print(f"  confidence  {metrics['avg_confidence']:.0%}")
print(f"  latency     {metrics['avg_latency_s']:.1f}s avg")
print(f"\n  by category:")
for cat, rate in sorted(metrics["per_category"].items()):
    n_cat = len(category_results[cat])
    passed_cat = sum(category_results[cat])
    print(f"    {cat:<25} {rate:.0%}  ({passed_cat}/{n_cat})")

prev = load_previous()
if prev:
    pm = prev["metrics"]
    print(f"\n  vs {prev['commit']} ({prev['branch']}):")
    print(f"    pass rate   {fmt_delta(metrics['pass_rate'], pm['pass_rate'])}")
    print(f"    fallback    {fmt_delta(metrics['fallback_rate'], pm['fallback_rate'], higher_is_better=False)}")
    print(f"    confidence  {fmt_delta(metrics['avg_confidence'], pm['avg_confidence'])}")
    print(f"    latency     {metrics['avg_latency_s'] - pm['avg_latency_s']:+.1f}s")
else:
    print(f"\n  (baseline established — future runs will show deltas)")

print(f"\n  saved → {out_path}")
print(f"{'='*w}")