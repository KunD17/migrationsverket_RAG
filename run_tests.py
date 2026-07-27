"""Run the personal test set against the RAG agent and report results.

Usage:
  python run_tests.py                        # run all categories
  python run_tests.py work_permit researcher  # narrow to specific categories
"""

import json
import sys
from migrationsverket_bot.agent.rag_agent import RAGAgent
from migrationsverket_bot.retrieval.embedder import Embedder
from migrationsverket_bot.retrieval.vector_store import VectorStore

TEST_SET_PATH = "migrationsverket_bot/evaluation/test_set_personal.json"

category_filter = set(sys.argv[1:]) or None

with open(TEST_SET_PATH) as f:
    tests = json.load(f)

if category_filter:
    tests = [t for t in tests if t.get("category") in category_filter]

agent = RAGAgent(vector_store=VectorStore(), embedder=Embedder())

passed = 0
failed = 0
failures = []

print(f"Running {len(tests)} tests...\n")

for test in tests:
    qid = test["id"]
    question = test["question"]
    must_contain = [kw.lower() for kw in test.get("must_contain", [])]
    must_not_contain = [kw.lower() for kw in test.get("must_not_contain", [])]

    print(f"[{qid}] {question[:80]}...")
    result = agent.answer(question)
    answer = result["answer"].lower()

    issues = []
    for kw in must_contain:
        if kw not in answer:
            issues.append(f"  MISSING: '{kw}'")
    for kw in must_not_contain:
        if kw in answer:
            issues.append(f"  SHOULD NOT CONTAIN: '{kw}'")

    if issues:
        failed += 1
        failures.append((qid, question, result["answer"], issues))
        print(f"  FAIL (confidence={result['confidence']:.0%})")
        for issue in issues:
            print(issue)
    else:
        passed += 1
        print(f"  PASS (confidence={result['confidence']:.0%})")
    print()

print("=" * 60)
print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
print("=" * 60)

if failures:
    print("\nFailed questions and answers:\n")
    for qid, question, answer, issues in failures:
        print(f"[{qid}] {question}")
        print(f"Answer: {answer[:300]}...")
        for issue in issues:
            print(issue)
        print()