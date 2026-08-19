# Milestone 5 Formal Evaluation Summary

- Benchmark: **acecqa_service_risk_copilot_formal_eval v1.1**
- Cases: **50**
- Passed: **50/50**
- Task Success Rate: **100.0%**
- Critical cases: **PASS**
- Milestone 5 ready: **YES**

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
| Avg Tokens / Query | 9290 |
| Avg Latency | 6.89s |
| Avg Tool Calls / Query | 1.02 |

## Category results

| Category | Passed | Rate |
|---|---:|---:|
| data_retrieval | 8/8 | 100.0% |
| risk_analysis | 8/8 | 100.0% |
| comparison | 6/6 | 100.0% |
| policy_rag | 8/8 | 100.0% |
| scenario_analysis | 8/8 | 100.0% |
| reliability_boundary | 12/12 | 100.0% |

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
