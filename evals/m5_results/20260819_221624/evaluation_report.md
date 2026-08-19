# Milestone 5 Formal Evaluation Summary

- Benchmark: **acecqa_service_risk_copilot_formal_eval v1.0**
- Cases: **1**
- Passed: **1/1**
- Task Success Rate: **100.0%**
- Critical cases: **PASS**
- Milestone 5 ready: **NO**

## Core metrics

| Metric | Result |
|---|---:|
| Tool Selection Accuracy | 100.0% |
| Tool Parameter Accuracy | 100.0% |
| Deterministic Output Accuracy | 100.0% |
| Numerical Accuracy | 100.0% |
| Evidence Grounding Accuracy | 100.0% |
| Policy Grounding Rate | 100.0% |
| Boundary Handling Rate | 100.0% |
| Avg Tokens / Query | 14123 |
| Avg Latency | 10.44s |
| Avg Tool Calls / Query | 2.00 |

## Category results

| Category | Passed | Rate |
|---|---:|---:|
| data_retrieval | 0/0 | n/a |
| risk_analysis | 0/0 | n/a |
| comparison | 0/0 | n/a |
| policy_rag | 0/0 | n/a |
| scenario_analysis | 0/0 | n/a |
| reliability_boundary | 1/1 | 100.0% |

## Acceptance checks

| Check | Actual | Target | Status |
|---|---:|---:|---|
| task_success_rate | 100.0% | >= 90.0% | PASS |
| tool_selection_accuracy | 100.0% | >= 94.0% | PASS |
| parameter_accuracy | 100.0% | >= 95.0% | PASS |
| deterministic_output_accuracy | 100.0% | >= 98.0% | PASS |
| numerical_accuracy | 100.0% | >= 100.0% | PASS |
| policy_grounding_rate | 100.0% | >= 95.0% | PASS |
| boundary_handling_rate | 100.0% | >= 92.0% | PASS |
| critical_cases | True | == True | PASS |

# Case-by-case results

| Case | Category | Critical | Status | Tools | Tokens | Latency |
|---|---|---:|---|---|---:|---:|
| M5-B04 | reliability_boundary | Yes | PASS | calculate_risk_score, search_policy | 14123 | 10.44s |

## Evaluation design notes

- v1.0 uses deterministic trace/output checks as the primary evaluator; it does not use an LLM-as-judge.
- Answer text checks are intentionally lightweight and are used mainly for reliability/boundary semantics.
- Policy grounding is validated from resolved policy chunk citations, not from model-written URLs.
- Cost is reported only when token prices are explicitly supplied at evaluation time.
- A benchmark PASS demonstrates performance on this fixed test set; it is not proof of regulatory validity or policy optimality.
