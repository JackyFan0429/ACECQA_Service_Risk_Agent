# ACECQA Service Risk Copilot

A B2B decision-support AI Agent evolved from the QBUS6860 spatial/data analysis project. The design principle is simple:

> **LLM decides what analysis to run; deterministic Python tools decide the numbers.**

## Current milestone: v0.2 Single Agent MVP

Milestone 2 connects the six validated analytics tools to a real single-agent tool-calling runtime using the OpenAI Agents SDK.

```text
Natural-language question
        |
        v
ACECQA Service Risk Copilot (single LLM agent)
        |
        | chooses one or more tools
        v
+-----------------------------------------+
| 6 deterministic Python analytics tools |
+-----------------------------------------+
        |
        v
education_services_cleaned.csv
17,663 service records
        |
        v
structured tool output
        |
        v
GroundedAgentAnswer
+ evidence + methodology + limitations
```

### Six tools

1. `search_services` — filtering, counts and factual listing
2. `get_service_profile` — one service's decision-relevant fields
3. `calculate_risk_score` — one service's validated 0–3 gap score
4. `find_high_risk_services` — deterministic regulatory priority ranking
5. `compare_transport_access` — aggregate transport-access comparison
6. `analyse_transport_quartile_outcomes` — NQS/capacity outcomes across transport quartiles

The original notebook remains in `notebooks/` for provenance. The analytics layer still reproduces the notebook's validated thresholds and risk logic.

## What changed in v0.2

- OpenAI Agents SDK single-agent runtime
- exact Pydantic schemas exposed as function tools
- model-visible success/error envelopes for every tool call
- structured final response (`GroundedAgentAnswer`)
- explicit grounding rule: data questions must call a deterministic tool
- application-level rejection of no-tool/ungrounded data runs
- auditable tool-call trace from SDK run items
- token-usage and latency capture for the future eval harness
- CLI demo for natural-language queries
- Runned smoke test for currenct agent

## Preserved risk definition

For the validated Centre-Based Care risk scope:

- poor transport access: nearest public transport distance >= national P75
- weak quality: overall NQS rating below Meeting NQS
- low authorised capacity: approved places <= national P25
- gap score: sum of those three binary flags (0–3)

Preserved values from the supplied notebook/data:

- national P75 transport threshold: ~5.329 km
- national P25 approved places threshold: 40
- national triple-gap services: 162
- QLD Rural CBC records in cleaned data: 227
- QLD Rural CBC services eligible for full risk analysis: 193
- QLD Rural CBC triple-gap services: 21

## Run the deterministic test suite

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

Expected for v0.2:

```text
13 passed
```

## Run the Single Agent MVP

Set an API key and optionally override the model:

```bash
export OPENAI_API_KEY="sk-..."
export ACECQA_AGENT_MODEL="gpt-5.6-terra"
```

Then run the milestone query:

```bash
python demo_agent.py \
  "Find the highest-risk rural Centre-Based Care services in Queensland." \
  --show-trace
```

Or return the full machine-readable run report:

```bash
python demo_agent.py \
  "Find the highest-risk rural Centre-Based Care services in Queensland." \
  --json
```

A grounded run should select `find_high_risk_services`, translate Queensland to `QLD`, use `Rural` + `Centre-Based Care`, and return evidence based on the deterministic tool result rather than model arithmetic.

## Reliability boundaries

- Risk thresholds are fixed from the national validated Centre-Based Care sample; state filters do not silently redefine them.
- `approved places` is authorised capacity, **not** observed demand, enrolment, utilisation, waitlists, or unmet need.
- Association is not causation.
- Risk model v1 is Centre-Based Care only.
- Policy RAG is intentionally not connected yet, so the agent must not invent ACECQA/NQS policy requirements or enforcement actions.

## Repository structure

```text
acecqa-risk-agent/
├── data/
│   └── education_services_cleaned.csv
├── notebooks/
│   └── QBUS6860_A1.ipynb
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DESIGN_DECISIONS.md
│   ├── TOOL_SCHEMAS.md
│   ├── MILESTONE_2.md
│   └── tool_schemas.json
├── src/acecqa_agent/
│   ├── config.py
│   ├── data_repository.py
│   ├── schemas.py
│   ├── agent/
│   │   ├── runtime.py
│   │   ├── openai_tools.py
│   │   ├── tool_adapter.py
│   │   ├── system_prompt.py
│   │   └── tool_registry.py
│   └── tools/
│       ├── common.py
│       ├── service_search.py
│       ├── risk_analysis.py
│       └── comparison.py
├── tests/
│   ├── test_tools.py
│   ├── test_agent_tool_adapter.py
│   └── test_agent_runtime_helpers.py
├── examples/
│   ├── qld_rural_top20.json
│   └── qld_rural_tool_envelope.json
├── demo_tools.py
├── demo_agent.py
├── .env.example
├── pyproject.toml
└── requirements.txt
```

## Next milestone

Milestone 3 will add **policy RAG as another tool**, not replace the deterministic data layer. The target becomes:

```text
structured service evidence
          +
ACECQA / NQS policy evidence
          |
          v
Agent recommendation with two-source grounding
```

Scenario analysis and formal evals come after that.
