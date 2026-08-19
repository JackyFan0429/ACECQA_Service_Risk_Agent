# Milestone 5 — Mac Run Guide

## 1. Install and regression-test

```bash
cd acecqa-risk-agent
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
python scripts/check_m5_benchmark.py
python scripts/check_policy_corpus.py
```

Expected merged M5 codebase regression result:

```text
32 passed
M5 benchmark integrity: PASS (50 cases)
Corpus integrity: PASS
```

## 2. Confirm benchmark contents without tokens

```bash
python run_m5_eval.py --list
```

## 3. Run a small live acceptance sample first

Data routing:

```bash
python run_m5_eval.py --case M5-D01
```

Data + policy boundary:

```bash
python run_m5_eval.py --case M5-B04
```

Scenario:

```bash
python run_m5_eval.py --case M5-S02
```

These are partial runs; `M5 ready` remains NO by design.

## 4. Run full 50-case formal evaluation

```bash
python run_m5_eval.py --pause 1
```

The full run can consume substantially more tokens than milestone smoke tests. Raw results are checkpointed after each case.

## 5. Resume after interruption

Find the latest folder:

```bash
ls -lt evals/m5_results
```

Then:

```bash
python run_m5_eval.py \
  --resume evals/m5_results/<timestamp> \
  --pause 1
```

## 6. Review

Upload `summary.md` first. If cases fail, also upload the corresponding `M5-*_raw.json` files.

The most useful files are:

```text
summary.md
evaluation_report.md
metrics.json
case_results.json
```

## 7. Re-score without API use

If the Agent run is correct but evaluator logic needs a bug fix:

```bash
python recheck_m5_results.py evals/m5_results/<timestamp>
```

This uses **0 new API tokens**.

### Retry transient API errors during resume

If a saved raw case contains a runtime/API error and should be retried:

```bash
python run_m5_eval.py \
  --resume evals/m5_results/<timestamp> \
  --retry-errors \
  --pause 1
```

Successful existing raw cases are still reused.
