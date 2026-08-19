# Milestone 3 Smoke Test Summary

- Passed: **8/8**
- Critical cases: **PASS**
- Milestone 3 ready: **YES**
- Total tokens: **77747**
- Cumulative API latency: **70.5s**

| Case | Critical | Status | Tools |
|---|---:|---|---|
| M3-01 | No | PASS | search_policy |
| M3-02 | Yes | PASS | search_policy |
| M3-03 | No | PASS | search_policy |
| M3-04 | Yes | PASS | find_high_risk_services, search_policy |
| M3-05 | Yes | PASS | calculate_risk_score, search_policy |
| M3-06 | No | PASS | search_policy |
| M3-07 | Yes | PASS | search_policy |
| M3-08 | Yes | PASS | calculate_risk_score, search_policy |

## Acceptance rule

Stable = at least 7/8 pass and all critical cases M3-02, M3-04, M3-05, M3-07, M3-08 pass.
