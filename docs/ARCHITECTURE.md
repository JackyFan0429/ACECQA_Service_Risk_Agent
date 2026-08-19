# Architecture — v0.4

## Product boundary

ACECQA Service Risk Copilot is a decision-support agent. The LLM orchestrates evidence; deterministic Python owns analytics and scenario arithmetic; a local policy corpus grounds regulatory context.

```text
                           User
                            |
                            v
                     Single LLM Agent
                            |
          +-----------------+------------------+
          |                 |                  |
          v                 v                  v
  Analytics tools    Scenario tools      search_policy
      (6)                (2)                (1)
          |                 |                  |
          +--------+--------+                  |
                   v                           v
        17,663 cleaned services        ACECQA/NQF corpus
                   |                           |
                   +-------------+-------------+
                                 v
                         Structured evidence
                                 |
                                 v
                        Grounding validator
                                 |
                                 v
                      Decision-support answer
```

## Nine tools

### Service / analytics

1. `search_services`
2. `get_service_profile`
3. `calculate_risk_score`
4. `find_high_risk_services`
5. `compare_transport_access`
6. `analyse_transport_quartile_outcomes`

### Scenario analysis

7. `simulate_risk_thresholds`
8. `compare_risk_scenarios`

### Policy

9. `search_policy`

## Scenario invariant

All transport/capacity percentiles are computed from the national validated Centre-Based Care risk sample. `state` or `urban_rural` only scopes the reported impact. This makes scenario thresholds comparable across jurisdictions and prevents silent redefinition of the model.

## Responsibility split

| Layer | Owns |
|---|---|
| LLM | intent parsing, tool selection, parameter mapping, explanation |
| Deterministic analytics | filtering, scoring, ranking, aggregations |
| Deterministic scenario layer | percentile thresholds, recomputed flags, A/B comparison, membership changes |
| Policy RAG | retrieving official policy/guidance passages |
| Runtime | tool trace, evidence validation, policy citation resolution, usage/latency telemetry |

## Reliability boundaries

- full dataset counts and risk-eligible counts are distinct
- risk model is Centre-Based Care only
- approved capacity is not demand
- association is not causation
- scenario sensitivity is not policy optimisation
- a threshold change does not prove causality or policy superiority
- risk score is not a legal non-compliance finding
- policy citations must correspond to actually retrieved chunks
