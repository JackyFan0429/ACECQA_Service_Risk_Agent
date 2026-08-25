# Milestone 4 — Scenario Analysis

## Goal

Upgrade the copilot from static prioritisation to deterministic decision simulation.

The agent may decide **which** scenario to run and explain its implications. Python alone computes percentile cut-offs, risk flags, counts, subgroup impacts, and service membership changes.

## New tools

### `simulate_risk_thresholds`

Compares one proposed threshold setting with the fixed v1 baseline:

- baseline transport = national P75
- baseline capacity = national P25
- weak-quality rule unchanged
- default priority definition = triple-gap (`minimum_gap_score=3`)

Example:

```json
{
  "transport_percentile": 0.80,
  "capacity_percentile": 0.25,
  "minimum_gap_score": 3,
  "state": "QLD",
  "urban_rural": "Rural"
}
```

### `compare_risk_scenarios`

Compares two arbitrary percentile assumption sets on the same validated Centre-Based Care sample.

Example:

```json
{
  "scenario_a": {
    "label": "Broad",
    "transport_percentile": 0.70,
    "capacity_percentile": 0.30,
    "minimum_gap_score": 3
  },
  "scenario_b": {
    "label": "Strict",
    "transport_percentile": 0.85,
    "capacity_percentile": 0.20,
    "minimum_gap_score": 3
  }
}
```

## Non-negotiable modelling rule

Percentile cut-offs are **always calculated on the national validated Centre-Based Care risk sample**. `state` and `urban_rural` only filter the population whose impact is reported.

This prevents a P80 threshold from silently meaning a different distance in QLD, NSW, Rural, or Urban subsets.

## Deterministic regression values

Using the current cleaned dataset:

| Scenario | National triple-gap pool |
|---|---:|
| P75 transport / P25 capacity | 162 |
| P80 / P25 | 149 |
| P70 / P30 | 196 |
| P85 / P20 | 111 |

For QLD Rural Centre-Based Care:

- eligible risk sample: 193
- baseline P75/P25 triple-gap: 21
- P80/P25 triple-gap: 20

## Interpretation boundary

Scenario analysis is a **sensitivity analysis**, not policy optimisation. A smaller priority pool does not prove a threshold is better, fairer, more efficient, causal, or legally appropriate.

## Offline Definition of Done

- two scenario tools registered with the agent
- Pydantic input/output schemas
- baseline regression reproduces 162 triple-gap services
- P80/P25 reproduces 149
- QLD Rural P80/P25 reproduces 20
- broad-vs-strict comparison reproduces 196 vs 111
- invalid percentiles rejected by schema
- all existing Milestone 1–3 offline tests remain green

Delivered code result: **25 offline tests passed**.

## Live acceptance

Run `run_m4_smoke_tests.py`. Stable means:

- at least 7/8 cases pass
- critical M4-02, M4-04, M4-06, M4-07, M4-08 all pass
