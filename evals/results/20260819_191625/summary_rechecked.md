# Milestone 2 Smoke Test Recheck

- Evaluator version: `1.1`
- Passed: **11/12**
- Critical cases: **PASS**
- Milestone 2 ready: **YES**
- Original run tokens: **61363** (recheck used 0 API tokens)
- Original cumulative latency: **80.8s**

| Case | Critical | Status | Tools |
|---|---:|---|---|
| M2-01 | No | PASS | find_high_risk_services |
| M2-02 | No | PASS | find_high_risk_services |
| M2-03 | Yes | PASS | search_services |
| M2-04 | No | PASS | search_services |
| M2-05 | No | FAIL | get_service_profile, calculate_risk_score |
| M2-06 | No | PASS | calculate_risk_score |
| M2-07 | No | PASS | compare_transport_access |
| M2-08 | No | PASS | analyse_transport_quartile_outcomes |
| M2-09 | Yes | PASS | none |
| M2-10 | Yes | PASS | find_high_risk_services |
| M2-11 | No | PASS | find_high_risk_services |
| M2-12 | Yes | PASS | none |

## Remaining failures

### M2-05
- Expected tools exactly ['get_service_profile'], got ['get_service_profile', 'calculate_risk_score'].


## Acceptance rule

Stable = at least 11/12 pass and M2-03, M2-09, M2-10, M2-12 all pass.

> M2-05 intentionally remains strict: an unnecessary extra risk-score call is still counted as a routing-efficiency miss.