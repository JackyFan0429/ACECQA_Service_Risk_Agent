# Milestone 5 — Formal Agent Evaluation

## Goal

Milestone 5 freezes product functionality and evaluates the complete ACECQA Service Risk Copilot as a system.

It does **not** add new analytics, policy, scenario, orchestration, or UI capability. The purpose is to answer:

> Does the Agent reliably choose the right tools, pass the right parameters, preserve deterministic numerical results, ground policy claims, and respect analytical/regulatory boundaries across a fixed benchmark?

## Benchmark

`evals/m5_benchmark.json` contains exactly **50 cases**:

| Category | Cases |
|---|---:|
| Data retrieval | 8 |
| Risk analysis / prioritisation | 8 |
| Comparison / quartile analysis | 6 |
| Policy RAG | 8 |
| Scenario analysis | 8 |
| Reliability / boundary handling | 12 |
| **Total** | **50** |

The benchmark reuses capabilities validated in M2–M4 but does not simply replay the milestone smoke tests. It includes paraphrases, new states, new threshold combinations, cross-tool composition, explicit scope errors, missing-data questions, causal traps, enforcement traps, and tool-efficiency checks.

## Primary evaluation design

M5 v1.0 deliberately does **not** use an LLM-as-judge.

Primary checks are deterministic and auditable:

1. actual tool trace;
2. exact/allowed tool selection;
3. Pydantic-compatible tool parameters;
4. deterministic tool output values;
5. numerical tolerances;
6. evidence source-tool references;
7. resolved ACECQA policy chunk citations and source domains;
8. lightweight semantic markers only for boundary statements that cannot be represented by tool output alone.

This avoids making evaluation correctness depend on a second model.

## Core metrics

The report calculates:

- **Task Success Rate** — percentage of benchmark cases passing all applicable checks.
- **Tool Selection Accuracy** — passed tool-routing checks / total tool-routing checks.
- **Tool Parameter Accuracy** — passed expected argument checks / total argument checks.
- **Deterministic Output Accuracy** — passed structured tool-output checks / total output checks.
- **Numerical Accuracy** — passed numerical output checks / total numerical output checks.
- **Evidence Grounding Accuracy** — expected evidence source tools actually cited by the structured final answer.
- **Policy Grounding Rate** — required resolved policy sources are present, official, and from the configured ACECQA domain.
- **Boundary Handling Rate** — percentage of `reliability_boundary` cases passing.
- average model requests, tokens/query, latency/query and tool calls/query.
- optional estimated cost/query when token prices are explicitly supplied by the evaluator operator.

## Acceptance rule

M5 v1.0 is marked `ready: YES` only when all configured checks pass:

- Task Success Rate >= **90%**
- Tool Selection Accuracy >= **94%**
- Tool Parameter Accuracy >= **95%**
- Deterministic Output Accuracy >= **98%**
- Numerical Accuracy = **100%**
- Policy Grounding Rate >= **95%**
- Boundary Handling Rate >= **92%**
- **all critical cases pass**

These thresholds are product acceptance criteria for this benchmark, not claims of regulatory validity.

## Run modes

List cases without API use:

```bash
python run_m5_eval.py --list
```

Run one case:

```bash
python run_m5_eval.py --case M5-D01
```

Run one category:

```bash
python run_m5_eval.py --category data_retrieval --pause 1
```

Full formal benchmark:

```bash
python run_m5_eval.py --pause 1
```

A partial run always reports `M5 ready: NO`, even if all selected cases pass.

## Resumability

Each case raw report is written immediately. If a long run is interrupted:

```bash
python run_m5_eval.py --resume evals/m5_results/<timestamp> --pause 1
```

Existing raw cases are reused. This prevents losing completed API work.

## 0-token recheck

After changing evaluator logic (not the Agent), re-score existing raw results without new API calls:

```bash
python recheck_m5_results.py evals/m5_results/<timestamp>
```

This produces `summary_rechecked.md`, `metrics_rechecked.json`, and `evaluation_report_rechecked.md`.

## Cost reporting

M5 never hard-codes current model prices. If cost reporting is desired, supply explicit rates:

```bash
python run_m5_eval.py \
  --pause 1 \
  --input-usd-per-1m <INPUT_PRICE> \
  --output-usd-per-1m <OUTPUT_PRICE>
```

or set:

```bash
export ACE_M5_INPUT_USD_PER_1M=<INPUT_PRICE>
export ACE_M5_OUTPUT_USD_PER_1M=<OUTPUT_PRICE>
```

The report then calculates total estimated cost and estimated cost/query from observed token usage.

## Outputs

Each run is stored under:

```text
evals/m5_results/<timestamp>/
├── M5-*_raw.json
├── case_results.json
├── metrics.json
├── summary.md
├── evaluation_report.md
└── run_config.json
```

`summary.md` is the quick acceptance view. `evaluation_report.md` is suitable as the source for README/evaluation documentation after the benchmark is frozen.
