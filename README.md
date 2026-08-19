# ACECQA Service Risk Copilot

A B2B decision-support AI Agent evolved from a QBUS6860 spatial/data analysis project.

> **The LLM decides what evidence or simulation it needs; deterministic Python decides the numbers; curated retrieval supplies policy context.**

## Current milestone: v0.4 Scenario Analysis

v0.4 preserves the stable analytics + policy-grounded agent from Milestones 1–3 and adds deterministic what-if analysis.

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
```

## Nine tools

1. `search_services` — factual filtering, counts and listing
2. `get_service_profile` — one service profile
3. `calculate_risk_score` — one service's validated 0–3 gap score
4. `find_high_risk_services` — deterministic priority ranking
5. `compare_transport_access` — aggregate transport comparison
6. `analyse_transport_quartile_outcomes` — quality/capacity across transport quartiles
7. `simulate_risk_thresholds` — compare a proposed threshold scenario with P75/P25 baseline
8. `compare_risk_scenarios` — deterministic A/B scenario comparison
9. `search_policy` — grounded retrieval from official ACECQA/NQF material

## Scenario design

The default validated model is not overwritten. Scenario tools recompute hypothetical flags on the same national valid Centre-Based Care sample.

**Invariant:** P80 always means the 80th percentile of the national validated Centre-Based Care risk sample. Filtering to QLD or Rural changes the impact population, not the threshold definition.

Current deterministic regression values:

- baseline P75 transport / P25 capacity: **162** national triple-gap services
- P80 / P25: **149** (`-13`)
- P70 / P30: **196**
- P85 / P20: **111**
- QLD Rural baseline: **21** triple-gap among **193** risk-eligible services
- QLD Rural P80/P25: **20**

Scenario output is sensitivity analysis. It does not prove that a threshold is optimal, causal, fair, legally appropriate, or a basis for enforcement.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Offline tests

```bash
pytest -q
```

Expected v0.4 result:

```text
25 passed
```

## Deterministic scenario demo — no API tokens

```bash
python demo_scenario.py --transport 0.80 --capacity 0.25
```

QLD Rural:

```bash
python demo_scenario.py \
  --transport 0.80 \
  --capacity 0.25 \
  --state QLD \
  --urban-rural Rural
```

## Live Agent scenario demo

```bash
export OPENAI_API_KEY="sk-..."
```

```bash
python demo_agent.py \
  "If poor transport changes from P75 to P80 while capacity stays P25, how does the national triple-gap priority pool change?" \
  --show-trace
```

Expected tool: `simulate_risk_thresholds`.

A/B comparison:

```bash
python demo_agent.py \
  "Compare a broad triple-gap scenario at P70 transport/P30 capacity with a strict scenario at P85/P20." \
  --show-trace
```

Expected tool: `compare_risk_scenarios`.

## Milestone 4 smoke test

```bash
python run_m4_smoke_tests.py --list
python run_m4_smoke_tests.py --case M4-02
python run_m4_smoke_tests.py --pause 1
```

Acceptance rule: at least **7/8** pass and all critical cases M4-02, M4-04, M4-06, M4-07 and M4-08 pass.

## Policy corpus

Milestone 3's policy corpus remains unchanged. The recommended ingestion path is the official versioned Guide to the NQF PDF:

```bash
python scripts/ingest_policy.py --pdf data/policy/raw/guide_to_nqf_2026_07.pdf
python scripts/check_policy_corpus.py
```

The Guide is guidance, not legal advice; the National Law and Regulations take precedence. State and territory regulatory authorities, not ACECQA, monitor and enforce service compliance.

## Project status

- Milestone 1 — deterministic analytics: complete
- Milestone 2 — Single Agent: passed (11/12, critical 4/4)
- Milestone 3 — policy-grounded Agent: passed (8/8, critical 5/5)
- Milestone 4 — scenario analysis: code ready; live acceptance pending
- Milestone 5 — formal 40–60 query Eval: next after v0.4 freezes
- Milestone 6 — FastAPI + frontend + Docker: final delivery stage

See `docs/MILESTONE_4.md`, `docs/SCENARIO_ANALYSIS.md`, and `docs/MILESTONE_4_INSTALL.md`.
