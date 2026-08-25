# Architecture

## Product boundary

ACECQA Service Risk Copilot is a decision-support Agent. The LLM orchestrates evidence; deterministic Python owns analytics and scenario arithmetic; a local policy corpus grounds regulatory context; the runtime validates evidence; M5 evaluates system behaviour; M6 exposes the same evaluated core through an HTTP product surface.

```text
                              Browser
                                 |
                                 v
                         FastAPI product API
                       /         |          \
                      v          v           v
               Static web UI  /api/chat  deterministic APIs
                                 |
                                 v
                          Single LLM Agent
                                 |
            +--------------------+--------------------+
            |                    |                    |
            v                    v                    v
     Analytics tools      Scenario tools        search_policy
          (6)                  (2)                  (1)
            |                    |                    |
            +----------+---------+                    |
                       v                              v
            17,663 cleaned services          ACECQA/NQF corpus
                       |                              |
                       +---------------+--------------+
                                       v
                               Structured evidence
                                       |
                                       v
                              Grounding validator
                                       |
                                       v
                            Decision-support answer
                                       |
                         +-------------+-------------+
                         |                           |
                         v                           v
                 Product telemetry            M5 evaluation plane
                                                    |
                          +-------------------------+----------------------+
                          |          |          |         |        |      |
                        routing    params     outputs   policy   boundary usage
                                                    |
                                                    v
                                           evaluation report
```

## Nine product tools

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

## M6 product surface

FastAPI adds no new decision logic. It adapts the frozen Agent/tool layer into:

- `/api/chat` — Agent orchestration
- `/api/services/{id}` — direct deterministic service lookup
- `/api/scenario` — direct deterministic scenario execution
- `/api/policy/search` — direct deterministic policy retrieval
- `/api/system/info` — reproducibility/evaluation metadata
- `/health` — process health

The frontend uses these HTTP endpoints and is served by the same process.

## Evaluation plane

`evals/m5_benchmark.json` defines the fixed 50-case benchmark. The completed v1.1 snapshot in this repository passed 50/50. The evaluator checks tool traces, parameters, deterministic outputs, policy sources and reliability boundaries; it does not use an LLM-as-judge.

## Scenario invariant

All transport/capacity percentiles are computed from the national validated Centre-Based Care risk sample. `state` or `urban_rural` only scopes the reported impact. This prevents silent subgroup redefinition and makes scenarios comparable.

## Responsibility split

| Layer | Owns |
|---|---|
| Web UI | user interaction and evidence display |
| FastAPI | HTTP contracts, errors, product metadata |
| LLM | intent parsing, tool selection, parameter mapping, explanation |
| Deterministic analytics | filtering, scoring, ranking, aggregations |
| Scenario layer | percentile thresholds, recomputed flags, A/B comparison |
| Policy RAG | local BM25 retrieval over official material |
| Runtime | trace, evidence validation, policy citation resolution, telemetry |
| M5 evaluator | benchmark routing/parameter/output/grounding/boundary metrics |
| Docker | reproducible single-container delivery |

## Reliability boundaries

- dataset counts and risk-eligible counts are distinct
- risk model v1 is Centre-Based Care only
- approved capacity is not demand
- association is not causation
- scenario sensitivity is not policy optimisation
- risk score is not a legal non-compliance finding
- policy citations must correspond to retrieved chunks
- formal benchmark performance does not imply regulatory validity
- product-mode no-tool responses are visibly labelled as boundary/interpretation responses
