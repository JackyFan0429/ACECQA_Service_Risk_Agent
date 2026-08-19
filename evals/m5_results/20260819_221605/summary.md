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
| Policy Grounding Rate | n/a |
| Boundary Handling Rate | n/a |
| Avg Tokens / Query | 7619 |
| Avg Latency | 5.49s |
| Avg Tool Calls / Query | 1.00 |

## Category results

| Category | Passed | Rate |
|---|---:|---:|
| data_retrieval | 1/1 | 100.0% |
| risk_analysis | 0/0 | n/a |
| comparison | 0/0 | n/a |
| policy_rag | 0/0 | n/a |
| scenario_analysis | 0/0 | n/a |
| reliability_boundary | 0/0 | n/a |

## Acceptance checks

| Check | Actual | Target | Status |
|---|---:|---:|---|
| task_success_rate | 100.0% | >= 90.0% | PASS |
| tool_selection_accuracy | 100.0% | >= 94.0% | PASS |
| parameter_accuracy | 100.0% | >= 95.0% | PASS |
| deterministic_output_accuracy | 100.0% | >= 98.0% | PASS |
| numerical_accuracy | 100.0% | >= 100.0% | PASS |
| policy_grounding_rate | None | >= 95.0% | FAIL |
| boundary_handling_rate | None | >= 92.0% | FAIL |
| critical_cases | True | == True | PASS |
