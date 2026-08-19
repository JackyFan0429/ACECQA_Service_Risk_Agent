# Agent Architecture — v0.1

## Product goal

**ACECQA Service Risk Copilot** is a decision-support agent for policy/regulatory analysts. The LLM does not calculate business-critical metrics itself. It interprets intent, chooses deterministic tools, and explains evidence returned by those tools.

## v0.1 architecture

```text
User
  |
  v
Single LLM Agent (orchestration only)
  |
  +--> search_services
  +--> get_service_profile
  +--> calculate_risk_score
  +--> find_high_risk_services
  +--> compare_transport_access
  +--> analyse_transport_quartile_outcomes
  |
  v
Deterministic Analytics Layer
  |
  v
education_services_cleaned.csv (17,663 services)
```

## Future architecture

```text
                         +---------------- Policy documents ----------------+
                         |                                                   |
User -> Single Agent ----+--> Analytics tools --> Structured service data    |
          |              |                                                   |
          |              +--> policy_search (RAG) <--------------------------+
          |
          +--> evidence/uncertainty check
          |
          +--> recommendation + data evidence + policy evidence + caveats
```

Later phases can add scenario tools, evals, FastAPI/Docker, then optionally MCP. Multi-agent is intentionally excluded from v0.1.

## Reliability rules

1. The LLM never computes risk thresholds, rankings, rates, or counts itself when a tool can do so.
2. v0.1 preserves the notebook's national CBC thresholds: poor transport = national CBC P75; low capacity = national CBC P25.
3. User filters (for example QLD/Rural) do **not** redefine those thresholds.
4. `approved places` is treated as authorised capacity, not demand or unmet need.
5. The risk score is only valid where transport, NQS quality, and approved-place data are available.
6. Ranking uses a visible deterministic tie-break rule; there are no hidden LLM weights.
