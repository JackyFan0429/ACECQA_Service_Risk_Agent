# Milestone 2 — Single Agent Tool-Calling MVP

## Definition of done

The milestone is complete at the code level when a natural-language user query can enter one single LLM agent, the model can choose from the six deterministic analytics tools, tool results are fed back into the model loop, and the final answer is returned with auditable evidence.

Target query:

> Find the highest-risk rural Centre-Based Care services in Queensland.

Expected orchestration intent:

```text
Queensland -> QLD
rural -> Rural
Centre-Based Care -> Centre-Based Care
highest-risk -> find_high_risk_services
no list size -> top_k=20
highest-risk -> minimum_gap_score=3
```

Expected deterministic facts for this query:

- 21 QLD Rural Centre-Based Care services satisfy all three gap conditions.
- The first ranked service is `SE-40000427` — Napranum Early Childhood Centre.
- Ranking policy is gap score DESC, transport distance DESC, approved places ASC, service approval number ASC.

## Runtime components

### `tool_adapter.py`

Framework-neutral contract layer. It validates JSON parameters with the existing Pydantic models, invokes deterministic functions, and returns a common envelope:

```json
{
  "ok": true,
  "tool": "find_high_risk_services",
  "data": {}
}
```

Errors are model-visible data rather than unhandled exceptions where recovery is possible:

```json
{
  "ok": false,
  "tool": "find_high_risk_services",
  "error_type": "ValueError",
  "message": "..."
}
```

### `openai_tools.py`

Converts the six contracts into OpenAI Agents SDK `FunctionTool` objects. The SDK receives the existing Pydantic JSON schemas and executes local Python through the adapter.

### `runtime.py`

Builds one agent and runs the tool-calling loop. It also:

- enforces structured `GroundedAgentAnswer` output;
- extracts tool calls and tool outputs from run items;
- rejects ungrounded data runs with no tool call;
- records latency and token usage for future evals.

### `system_prompt.py`

Contains business and reliability rules, including:

- no LLM arithmetic/ranking when a deterministic tool exists;
- stable national thresholds;
- CBC-only risk model;
- authorised capacity != unmet demand;
- association != causation;
- no policy claims before policy RAG is connected.

## Verification status

### Verified offline in this repository

- original notebook risk regressions
- all six deterministic tools
- tool registry metadata
- JSON/Pydantic validation
- QLD Rural triple-gap priority invocation
- structured tool errors
- tool trace extraction helper

Current suite: **13 tests passed**.

### Requires a local API key

The actual model-selection step cannot be exercised without `OPENAI_API_KEY`. Run:

```bash
pip install -e ".[dev]"
export OPENAI_API_KEY="sk-..."
python demo_agent.py \
  "Find the highest-risk rural Centre-Based Care services in Queensland." \
  --show-trace
```

The trace should show a `find_high_risk_services` call followed by its deterministic JSON output and then the model's grounded final response.

## Acceptance checks for the first live run

1. The model chooses `find_high_risk_services` rather than `search_services` + manual ranking.
2. It passes `state="QLD"`, `urban_rural="Rural"`, `service_type="Centre-Based Care"`.
3. It uses `minimum_gap_score=3` and `top_k=20` for the target wording.
4. Tool output reports 21 matching triple-gap services.
5. The final answer does not alter any returned numeric value.
6. Evidence names only tools actually used in the trace.
7. The answer includes the approved-capacity limitation and does not make policy claims.
