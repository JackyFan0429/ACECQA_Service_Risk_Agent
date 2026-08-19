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
