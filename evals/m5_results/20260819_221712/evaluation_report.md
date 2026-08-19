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

# Case-by-case results

| Case | Category | Critical | Status | Tools | Tokens | Latency |
|---|---|---:|---|---|---:|---:|
| M5-D01 | data_retrieval | Yes | PASS | search_services | 7667 | 5.90s |
| M5-D02 | data_retrieval | No | PASS | search_services | 14650 | 5.16s |
| M5-D03 | data_retrieval | No | PASS | search_services | 14798 | 4.32s |
| M5-D04 | data_retrieval | No | PASS | search_services | 9570 | 4.02s |
| M5-D05 | data_retrieval | No | PASS | get_service_profile | 7738 | 5.66s |
| M5-D06 | data_retrieval | No | PASS | get_service_profile | 7615 | 3.41s |
| M5-D07 | data_retrieval | No | PASS | search_services | 7604 | 4.20s |
| M5-D08 | data_retrieval | No | PASS | search_services | 14923 | 4.33s |
| M5-R01 | risk_analysis | Yes | PASS | calculate_risk_score | 7811 | 6.30s |
| M5-R02 | risk_analysis | No | PASS | calculate_risk_score | 7706 | 5.26s |
| M5-R03 | risk_analysis | Yes | PASS | find_high_risk_services | 8522 | 7.76s |
| M5-R04 | risk_analysis | No | PASS | find_high_risk_services | 8619 | 7.68s |
| M5-R05 | risk_analysis | No | PASS | find_high_risk_services | 8334 | 5.95s |
| M5-R06 | risk_analysis | No | PASS | find_high_risk_services | 8515 | 6.89s |
| M5-R07 | risk_analysis | No | PASS | calculate_risk_score | 7800 | 5.55s |
| M5-R08 | risk_analysis | No | PASS | find_high_risk_services | 8427 | 6.81s |
| M5-C01 | comparison | Yes | PASS | compare_transport_access | 7691 | 15.66s |
| M5-C02 | comparison | No | PASS | compare_transport_access | 8030 | 5.04s |
| M5-C03 | comparison | No | PASS | compare_transport_access | 7720 | 4.70s |
| M5-C04 | comparison | No | PASS | analyse_transport_quartile_outcomes | 8010 | 5.87s |
| M5-C05 | comparison | No | PASS | analyse_transport_quartile_outcomes | 7974 | 5.24s |
| M5-C06 | comparison | No | PASS | compare_transport_access | 7716 | 5.54s |
| M5-P01 | policy_rag | Yes | PASS | search_policy | 9235 | 6.27s |
| M5-P02 | policy_rag | Yes | PASS | search_policy | 9631 | 6.89s |
| M5-P03 | policy_rag | No | PASS | search_policy | 11193 | 8.07s |
| M5-P04 | policy_rag | Yes | PASS | search_policy | 9820 | 6.26s |
| M5-P05 | policy_rag | No | PASS | search_policy | 9684 | 5.35s |
| M5-P06 | policy_rag | No | PASS | search_policy | 9952 | 7.29s |
| M5-P07 | policy_rag | No | PASS | search_policy | 17250 | 7.41s |
| M5-P08 | policy_rag | No | PASS | search_policy | 10916 | 16.95s |
| M5-S01 | scenario_analysis | No | PASS | simulate_risk_thresholds | 8341 | 5.89s |
| M5-S02 | scenario_analysis | Yes | PASS | simulate_risk_thresholds | 9218 | 7.01s |
| M5-S03 | scenario_analysis | No | PASS | simulate_risk_thresholds | 8331 | 7.32s |
| M5-S04 | scenario_analysis | Yes | PASS | compare_risk_scenarios | 9503 | 8.24s |
| M5-S05 | scenario_analysis | No | PASS | simulate_risk_thresholds | 9252 | 15.05s |
| M5-S06 | scenario_analysis | No | PASS | simulate_risk_thresholds | 8354 | 5.65s |
| M5-S07 | scenario_analysis | No | PASS | compare_risk_scenarios | 10025 | 6.89s |
| M5-S08 | scenario_analysis | No | PASS | simulate_risk_thresholds | 9094 | 5.90s |
| M5-B01 | reliability_boundary | Yes | PASS | none | 3754 | 3.12s |
| M5-B02 | reliability_boundary | Yes | PASS | none | 3772 | 2.52s |
| M5-B03 | reliability_boundary | Yes | PASS | find_high_risk_services | 7679 | 5.63s |
| M5-B04 | reliability_boundary | Yes | PASS | calculate_risk_score, search_policy | 14126 | 10.40s |
| M5-B05 | reliability_boundary | Yes | PASS | search_policy | 9662 | 7.02s |
| M5-B06 | reliability_boundary | Yes | PASS | search_policy | 9598 | 6.36s |
| M5-B07 | reliability_boundary | Yes | PASS | analyse_transport_quartile_outcomes | 8211 | 8.66s |
| M5-B08 | reliability_boundary | Yes | PASS | simulate_risk_thresholds, search_policy | 15257 | 13.84s |
| M5-B09 | reliability_boundary | Yes | PASS | simulate_risk_thresholds | 8596 | 8.40s |
| M5-B10 | reliability_boundary | No | PASS | get_service_profile | 7446 | 3.98s |
| M5-B11 | reliability_boundary | No | PASS | none | 3764 | 3.57s |
| M5-B12 | reliability_boundary | Yes | PASS | find_high_risk_services, search_policy | 15373 | 13.38s |

## Evaluation design notes

- The evaluator uses deterministic trace/output checks as the primary evaluator; it does not use an LLM-as-judge.
- Answer text checks are intentionally lightweight and are used mainly for reliability/boundary semantics.
- Policy grounding is validated from resolved policy chunk citations, not from model-written URLs.
- Cost is reported only when token prices are explicitly supplied at evaluation time.
- A benchmark PASS demonstrates performance on this fixed test set; it is not proof of regulatory validity or policy optimality.
