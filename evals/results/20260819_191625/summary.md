# Milestone 2 Smoke Test Summary

- Model: `gpt-5.6-terra`
- Passed: **8/12**
- Critical cases: **FAIL**
- Milestone 2 ready: **NO**
- Total tokens: **61363**
- Cumulative API latency: **80.8s**

| Case | Critical | Status | Tools |
|---|---:|---|---|
| M2-01 | No | PASS | find_high_risk_services |
| M2-02 | No | PASS | find_high_risk_services |
| M2-03 | Yes | PASS | search_services |
| M2-04 | No | PASS | search_services |
| M2-05 | No | FAIL | get_service_profile, calculate_risk_score |
| M2-06 | No | FAIL | calculate_risk_score |
| M2-07 | No | PASS | compare_transport_access |
| M2-08 | No | PASS | analyse_transport_quartile_outcomes |
| M2-09 | Yes | FAIL | none |
| M2-10 | Yes | PASS | find_high_risk_services |
| M2-11 | No | PASS | find_high_risk_services |
| M2-12 | Yes | FAIL | none |

## Failures

### M2-05
- Expected tools exactly ['get_service_profile'], got ['get_service_profile', 'calculate_risk_score'].

### M2-06
- Answer did not contain any of the required alternatives: ['3/3', 'gap score 3', 'score of 3', '3 gaps', 'triple-gap'].

### M2-09
- Answer did not contain any of the required alternatives: ['cannot', 'does not', "doesn't", 'not enough', 'insufficient', 'cannot conclude'].

### M2-12
- Answer did not contain any of the required alternatives: ['cannot', "can't", 'not available', 'does not contain', "doesn't contain", 'no data', 'insufficient'].


## Acceptance rule

Milestone 2 is considered stable when at least 11/12 cases pass and all four critical cases (M2-03, M2-09, M2-10, M2-12) pass.

> Boundary answer checks are intentionally lightweight string checks. Review the raw answer files for M2-09, M2-10 and M2-12 before freezing v0.2.