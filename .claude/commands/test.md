# Run the test suite

```bash
python run_tests.py
```

Runs 16 questions from `migrationsverket_bot/evaluation/test_set_personal.json` and checks answers against `must_contain` / `must_not_contain` keyword lists. Prints PASS/FAIL per question with confidence score, then a summary.

Unlike `benchmark.py`, this does not save results to disk or track deltas — use it for quick feedback during development.

Use `python benchmark.py` when you want a saved, comparable record of a run.
