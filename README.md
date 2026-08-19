# ACECQA Service Risk Copilot

A B2B decision-support AI Agent evolved from a QBUS6860 spatial/data analysis project.

> **The LLM decides what evidence or simulation it needs; deterministic Python decides the numbers; curated retrieval supplies policy context; the formal evaluator checks whether the whole system behaved correctly.**

## Current milestone: v0.5 Formal Evaluation

Milestones 1–4 are feature-frozen. v0.5 adds a reproducible **50-case system-level benchmark** and evaluation/reporting harness; it does not add new product capabilities.

```text
Natural-language question
        |
        v
Single LLM Agent
   /       |        \
  v        v         v
Analytics Scenario   Policy RAG
 tools     tools     search_policy
  \        |         /
   +-------+--------+
           v
  Grounded decision support
           |
           v
      M5 Evaluator
   /    /    |     \
route args numbers grounding boundaries
```

## Nine product tools

1. `search_services`
2. `get_service_profile`
3. `calculate_risk_score`
4. `find_high_risk_services`
5. `compare_transport_access`
6. `analyse_transport_quartile_outcomes`
7. `simulate_risk_thresholds`
8. `compare_risk_scenarios`
9. `search_policy`

## M5 formal benchmark

`evals/m5_benchmark.json` contains **50 cases**:

- 8 data retrieval
- 8 risk analysis
- 6 comparison
- 8 policy RAG
- 8 scenario analysis
- 12 reliability/boundary

The evaluator reports:

- Task Success Rate
- Tool Selection Accuracy
- Tool Parameter Accuracy
- Deterministic Output Accuracy
- Numerical Accuracy
- Evidence Grounding Accuracy
- Policy Grounding Rate
- Boundary Handling Rate
- average tokens/query
- average latency/query
- average tool calls/query
- optional estimated cost/query when token prices are supplied explicitly

v1.0 primarily evaluates structured traces and deterministic outputs. It deliberately does **not** use an LLM-as-judge.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Offline regression before API use

```bash
pytest -q
python scripts/check_m5_benchmark.py
python scripts/check_policy_corpus.py
```

Expected v0.5 code regression:

```text
32 passed
M5 benchmark integrity: PASS (50 cases)
Corpus integrity: PASS
```

## Formal evaluation

List the benchmark without tokens:

```bash
python run_m5_eval.py --list
```

Run one development case:

```bash
python run_m5_eval.py --case M5-D01
```

Run the full benchmark:

```bash
export OPENAI_API_KEY="sk-..."
python run_m5_eval.py --pause 1
```

A partial run is never marked M5-ready. The full suite is evaluated against the acceptance thresholds in `evals/m5_benchmark.json`.

## Resume and 0-token recheck

Runs checkpoint every raw case under `evals/m5_results/<timestamp>/`.

Resume:

```bash
python run_m5_eval.py --resume evals/m5_results/<timestamp> --pause 1
```

Re-score existing results without new API calls:

```bash
python recheck_m5_results.py evals/m5_results/<timestamp>
```

## Optional cost/query

The project does not hard-code model prices. Supply current rates yourself when you want cost reporting:

```bash
python run_m5_eval.py \
  --pause 1 \
  --input-usd-per-1m <INPUT_PRICE> \
  --output-usd-per-1m <OUTPUT_PRICE>
```

## Stable product regression values

- cleaned services: **17,663**
- v1 national CBC P75 transport: **5.329340 km**
- v1 national CBC P25 capacity: **40 places**
- national baseline triple-gap: **162**
- P80/P25 scenario: **149**
- P70/P30: **196**
- P85/P20: **111**
- QLD Rural CBC dataset count: **227**
- QLD Rural risk-eligible sample: **193**
- QLD Rural baseline triple-gap: **21**
- local policy corpus: **1,395 chunks** from the versioned official Guide snapshot in this repo

## Project status

- Milestone 1 — deterministic analytics: ✅ complete
- Milestone 2 — Single Agent: ✅ passed (11/12, critical 4/4)
- Milestone 3 — policy-grounded Agent: ✅ passed (8/8, critical 5/5)
- Milestone 4 — scenario analysis: ✅ passed (8/8, critical 5/5)
- Milestone 5 — formal 50-case evaluation: 🟡 harness ready; live benchmark pending
- Milestone 6 — FastAPI + frontend + Docker: next after M5 freezes

See `docs/MILESTONE_5.md`, `docs/EVALUATION.md`, and `docs/MILESTONE_5_INSTALL.md`.
