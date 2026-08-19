# ACECQA Service Risk Copilot

A B2B decision-support AI Agent evolved from the QBUS6860 spatial/data analysis project.

> **LLM decides which evidence it needs; deterministic analytics decide the numbers; curated retrieval supplies policy context.**

## Current milestone: v0.3 Policy-grounded Single Agent

Milestone 3 keeps the six deterministic service-analysis tools from v0.2 and adds a seventh tool, `search_policy`, backed by a curated local corpus built from official ACECQA/NQF pages.

```text
Natural-language question
        |
        v
Single LLM Agent
        |
        +-----------------------------+
        |                             |
        v                             v
6 deterministic                search_policy()
analytics tools                local BM25 retrieval
        |                             |
        v                             v
service data                    curated ACECQA/NQF corpus
        |                             |
        +-------------+---------------+
                      v
              GroundedAgentAnswer
       data evidence + policy evidence
       + methodology + limitations
```

## Seven tools

1. `search_services` — filtering, counts and factual listing
2. `get_service_profile` — one service's decision-relevant fields
3. `calculate_risk_score` — one service's validated 0–3 gap score
4. `find_high_risk_services` — deterministic regulatory-priority ranking
5. `compare_transport_access` — aggregate transport-access comparison
6. `analyse_transport_quartile_outcomes` — NQS/capacity outcomes across transport quartiles
7. `search_policy` — grounded retrieval from curated official ACECQA/NQF material

## Why policy RAG is a tool

The LLM is not allowed to invent policy. When a user asks what an NQS rating means, what a regulatory authority should consider, or what compliance tools exist, it must call `search_policy`. When a user asks for both a risk priority list and regulatory context, it must combine an analytics tool with `search_policy`.

Policy retrieval cannot modify the deterministic risk score or ranking.

## Regulatory boundary

The project uses the name ACECQA Service Risk Copilot because ACECQA is the national quality authority and the principal source used for NQF guidance. However, ACECQA is not the national regulator. State and territory regulatory authorities assess and rate services and monitor/enforce compliance under the NQF. The agent therefore uses "the relevant regulatory authority" when discussing possible regulatory response.

A triple-gap score is a prioritisation signal, **not** evidence of a breach and **not** an automatic enforcement trigger.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 1. Build the policy corpus

The repository contains an allow-list of official sources in `data/policy/sources.json`. Fetch and chunk them locally:

```bash
python scripts/ingest_policy.py
python scripts/check_policy_corpus.py
```

This creates:

```text
data/policy/policy_chunks.jsonl
data/policy/corpus_manifest.json
```

The generated corpus is intentionally not the source of truth forever. Refresh it before an important demo because ACECQA guidance and legislation can change.

## 2. Test retrieval without an LLM

```bash
python demo_policy_search.py \
  "What should regulators consider before deciding how to respond to a compliance issue?"
```

You should see ACECQA source URLs, section names, stable `POL-...` chunk IDs and BM25 scores.

## 3. Run all offline tests

```bash
pytest -q
```

Expected for v0.3 code delivered in this milestone:

```text
19 passed
```

## 4. Run the live agent

```bash
export OPENAI_API_KEY="sk-..."
export ACECQA_AGENT_MODEL="gpt-5.6-terra"
```

Policy-only question:

```bash
python demo_agent.py \
  "What does a Working Towards NQS rating mean?" \
  --show-trace
```

Two-source decision-support question:

```bash
python demo_agent.py \
  "Find the 5 highest-risk rural Centre-Based Care services in Queensland and explain what the relevant regulatory authority should consider before deciding how to respond." \
  --show-trace
```

The second query should call both `find_high_risk_services` and `search_policy`.

## 5. Milestone 3 live smoke test

List the eight cases without spending API tokens:

```bash
python run_m3_smoke_tests.py --list
```

Run one critical case first:

```bash
python run_m3_smoke_tests.py --case M3-04
```

Then run the complete suite:

```bash
python run_m3_smoke_tests.py
```

Acceptance rule: at least **7/8** pass and all five critical cases pass.

## Policy grounding design

`search_policy` returns structured chunks containing:

- stable `chunk_id`
- source title
- official source URL
- section heading
- authority/source type
- retrieved excerpt
- retrieval score
- corpus retrieval timestamp

The LLM must put returned chunk IDs into structured policy evidence. The runtime checks those IDs against the actual tool output. A fabricated policy chunk ID therefore causes a grounding failure. Human-readable source titles and URLs are then resolved by application code from the tool trace instead of being trusted from model text.

## Preserved risk definition

For the validated Centre-Based Care risk scope:

- poor transport access: nearest public transport distance >= national P75
- weak quality: overall NQS rating below Meeting NQS
- low authorised capacity: approved places <= national P25
- gap score: sum of those three binary flags (0–3)

Preserved values from the original notebook/data:

- national P75 transport threshold: ~5.329 km
- national P25 approved places threshold: 40
- national triple-gap services: 162
- QLD Rural CBC records in cleaned data: 227
- QLD Rural CBC services eligible for full risk analysis: 193
- QLD Rural CBC triple-gap services: 21

## Repository structure

```text
acecqa-risk-agent/
├── data/
│   ├── education_services_cleaned.csv
│   └── policy/
│       ├── sources.json
│       ├── policy_chunks.jsonl        # generated locally
│       └── corpus_manifest.json       # generated locally
├── src/acecqa_agent/
│   ├── rag/
│   │   └── policy_repository.py
│   ├── tools/
│   │   ├── service_search.py
│   │   ├── risk_analysis.py
│   │   ├── comparison.py
│   │   └── policy_search.py
│   └── agent/
│       ├── runtime.py
│       ├── openai_tools.py
│       ├── tool_adapter.py
│       └── system_prompt.py
├── scripts/
│   ├── ingest_policy.py
│   └── check_policy_corpus.py
├── evals/
│   ├── smoke_cases.json
│   └── m3_cases.json
├── docs/
│   ├── MILESTONE_2.md
│   ├── MILESTONE_3.md
│   ├── POLICY_CORPUS.md
│   └── ARCHITECTURE.md
├── demo_agent.py
├── demo_policy_search.py
└── run_m3_smoke_tests.py
```

## Next milestone after v0.3

Once policy retrieval and two-source grounding pass the Milestone 3 smoke test, the next product feature is **Scenario Analysis**: allow an analyst to change transport/capacity thresholds and compare how the priority population changes without altering the validated default model.
