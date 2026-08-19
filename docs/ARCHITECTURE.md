# Agent Architecture — v0.2

## Product goal

**ACECQA Service Risk Copilot** is a decision-support agent for policy/regulatory analysts. The LLM owns intent interpretation and tool orchestration; deterministic Python owns filtering, arithmetic, risk scoring, aggregation, and ranking.

## Milestone 2 runtime

```text
User natural-language question
        |
        v
+------------------------------------------+
| ACECQA Service Risk Copilot              |
| OpenAI Agents SDK / Responses runtime    |
| Single agent only                        |
+------------------------------------------+
        |
        | function tool call(s)
        v
+------------------------------------------+
| Agent Tool Adapter                       |
| - exact Pydantic input schema            |
| - validation                             |
| - success/error envelope                 |
+------------------------------------------+
        |
        v
+------------------------------------------+
| Deterministic Analytics Layer            |
| search / profile / risk / rank / compare |
+------------------------------------------+
        |
        v
education_services_cleaned.csv
17,663 rows
        |
        v
structured tool output
        |
        v
Agent loop receives evidence
        |
        v
GroundedAgentAnswer
- direct answer
- evidence -> source_tool
- methodology
- limitations
        |
        v
Application grounding check
(no-tool data run => rejected)
```

## Why the adapter is separate from the LLM SDK

The analytics functions do not import any LLM framework. `tool_adapter.py` is the stable boundary that converts JSON arguments into Pydantic inputs and returns JSON-safe deterministic outputs. `openai_tools.py` is a thin SDK-specific wrapper.

That means a later MCP server or LangGraph workflow can reuse the same analytics contracts without rewriting business logic.

## Tool-selection policy

| Intent | Tool |
|---|---|
| Filter/count/list services | `search_services` |
| Inspect one exact service | `get_service_profile` |
| Score one exact service | `calculate_risk_score` |
| Highest-risk / investigate-first / priority list | `find_high_risk_services` |
| Compare transport access across groups | `compare_transport_access` |
| Analyse quality/capacity across transport quartiles | `analyse_transport_quartile_outcomes` |

For the milestone phrase **"highest-risk"**, the agent is instructed to use `minimum_gap_score=3` unless the user asks for a broader candidate pool. If list size is omitted, `top_k=20` is the product default.

## Grounded output contract

The final model output is structured as:

```text
GroundedAgentAnswer
├── answer
├── evidence[]
│   ├── source_tool
│   └── claim
├── methodology[]
└── limitations[]
```

`source_tool` is restricted to the six registered tools. The runtime also inspects SDK `new_items` to produce a tool trace and rejects data runs that contain no tool call.

## Observability already captured

Each `AgentRunReport` records:

- selected model
- tools used
- tool call/output trace
- final structured answer
- LLM request count
- input/output/total tokens
- end-to-end latency

This is intentionally added now so milestone 5 evals do not require redesigning the runtime.

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

Scenario tools, evals, FastAPI/Docker, and optional MCP come later. Multi-agent remains intentionally excluded.
