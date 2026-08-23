# ACECQA Service Risk Copilot

A portfolio-grade B2B decision-support AI Agent evolved from a QBUS6860 spatial/data analysis project.

The product helps an education-and-care policy or regulatory analyst move from a natural-language question to auditable data evidence, policy context, and scenario analysis without asking the LLM to perform critical numerical calculations itself.

> **The LLM decides what evidence or simulation it needs; deterministic Python decides the numbers; curated retrieval supplies policy context; the runtime validates grounding; a formal benchmark checks system behaviour.**

## Product status

**v0.6 — Productised demo**

- Milestone 1 — deterministic analytics: ✅ complete
- Milestone 2 — Single Agent: ✅ passed (11/12, critical 4/4)
- Milestone 3 — policy-grounded Agent: ✅ passed (8/8, critical 5/5)
- Milestone 4 — scenario analysis: ✅ passed (8/8, critical 5/5)
- Milestone 5 — formal evaluation: ✅ passed (**50/50**, critical PASS)
- Milestone 6 — FastAPI + web demo + Docker packaging: ✅ code complete; local product regression passed

## What the product can do

### 1. Service discovery and profiling

Ask questions such as:

> How many rural Centre-Based Care services are there in Queensland?

The Agent routes to deterministic filtering rather than estimating the answer in-model.

### 2. Risk prioritisation

> Find the five highest-risk rural Centre-Based Care services in Queensland.

The current v1 screen combines three validated assignment-derived signals:

- poor public-transport access
- Below Meeting NQS quality outcome
- low authorised capacity

The score is a **prioritisation signal**, not a legal finding of non-compliance.

### 3. Policy-grounded interpretation

> What should the relevant regulatory authority consider before deciding how to respond?

`search_policy()` retrieves from a local, versioned ACECQA Guide to the NQF snapshot. Policy claims must cite chunk IDs that were actually returned in the tool trace.

### 4. Scenario analysis

> What happens if poor transport changes from P75 to P80 while capacity stays at P25?

The LLM does not calculate the result. Python recomputes thresholds and priority-pool membership deterministically.

### 5. Reliability boundaries

The Agent is explicitly tested not to infer that:

- authorised capacity equals demand, utilisation, vacancies or waitlists
- association implies causation
- Working Towards NQS automatically means unsafe care
- a triple-gap score establishes legal non-compliance
- a smaller scenario pool proves a better policy
- subgroup filters can silently redefine the national percentile thresholds

## Architecture

```text
Browser / API client
        |
        v
     FastAPI
   /    |     \
  v     v      v
Web   Agent   Deterministic endpoints
UI    runtime  (service/scenario/policy)
       |
       v
  Single LLM Agent
   /       |        \
  v        v         v
Analytics Scenario   Policy RAG
 tools     tools     search_policy
  \        |         /
   +-------+--------+
           v
  Grounded decision support
           |
           v
   Audit trace + telemetry
           |
           v
  50-case M5 evaluator
```

## Nine product tools

1. `search_services`
2. `get_service_profile`
3. `calculate_risk_score`
4. `find_high_risk_services`
5. `compare_transport_access`
6. `analyse_transport_quartile_outcomes`
7. `simulate_risk_thresholds`
8. `compare_risk_scenarios`
9. `search_policy`

## Formal evaluation — v1.1

The fixed 50-query benchmark is stored in `evals/m5_benchmark.json`.

| Metric | Result |
|---|---:|
| Task Success Rate | **100.0%** |
| Tool Selection Accuracy | **100.0%** |
| Tool Parameter Accuracy | **100.0%** |
| Deterministic Output Accuracy | **100.0%** |
| Numerical Accuracy | **100.0%** |
| Evidence Grounding Accuracy | **100.0%** |
| Policy Grounding Rate | **100.0%** |
| Boundary Handling Rate | **100.0%** |
| Average tokens/query | 9,290 |
| Average latency/query | 6.89 s |
| Average tool calls/query | 1.02 |

Category results:

- data retrieval: 8/8
- risk analysis: 8/8
- comparison: 6/6
- policy RAG: 8/8
- scenario analysis: 8/8
- reliability/boundary: 12/12

These results are from a fixed benchmark snapshot. They are **not** proof of regulatory validity, real-world policy optimality, or autonomous decision-making capability.

## Stable product regression values

- cleaned services: **17,663**
- national CBC P75 transport threshold: **5.329340 km**
- national CBC P25 capacity threshold: **40 places**
- national baseline triple-gap pool: **162**
- P80/P25 scenario: **149**
- P70/P30 scenario: **196**
- P85/P20 scenario: **111**
- QLD Rural CBC dataset count: **227**
- QLD Rural risk-eligible sample: **193**
- QLD Rural baseline triple-gap: **21**
- local policy corpus: **1,395 chunks**

## Local quick start

Python 3.10+ is supported. Python 3.12 is used in the Docker image.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

export OPENAI_API_KEY="your-key"
python run_api.py
```

Open:

- product demo: `http://localhost:8000`
- OpenAPI / Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- health check: `http://localhost:8000/health`

The service lookup, scenario endpoint, policy retrieval, health check and system-info endpoint are deterministic and do not require an OpenAI call. `/api/chat` requires an API key.

## Docker

Copy the environment template:

```bash
cp .env.example .env
# edit .env and add OPENAI_API_KEY
```

Then:

```bash
docker compose up --build
```

Open `http://localhost:8000`.

The project intentionally uses one FastAPI container that also serves the lightweight frontend. This keeps the demo easy to reproduce while preserving a real HTTP API boundary.

## API surface

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | process health |
| GET | `/api/system/info` | dataset, corpus, tools and evaluation snapshot |
| POST | `/api/chat` | full Agent orchestration |
| GET | `/api/services/{service_id}` | deterministic service profile |
| POST | `/api/scenario` | deterministic threshold sensitivity analysis |
| POST | `/api/policy/search` | deterministic local BM25 policy retrieval |

Example:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "Find the 5 highest-risk rural Centre-Based Care services in Queensland and explain what the relevant regulatory authority should consider before deciding how to respond."
  }'
```

## Product demo

The browser demo includes:

- natural-language Copilot
- example prompt shortcuts
- tool/evidence/policy-source panels
- usage and latency telemetry
- expandable tool trace
- deterministic Scenario Lab
- direct service lookup
- live product/evaluation stats

The frontend renders model content as text rather than injecting model-produced HTML.

## Regression and integrity checks

```bash
pytest -q
python scripts/check_m5_benchmark.py
python scripts/check_policy_corpus.py
python scripts/check_m6_product.py
```

Expected v0.6 regression:

```text
42 passed
M5 benchmark integrity: PASS (50 cases)
Corpus integrity: PASS
M6 product integrity: PASS
```

## Project structure

```text
acecqa-risk-agent/
├── data/
│   ├── education_services_cleaned.csv
│   └── policy/
├── evals/
│   ├── m5_benchmark.json
│   └── m5_results/
├── frontend/
│   ├── index.html
│   └── assets/
├── src/acecqa_agent/
│   ├── agent/
│   ├── api/                 # M6 FastAPI product surface
│   ├── evals/
│   ├── rag/
│   └── tools/
├── tests/
├── docs/
├── Dockerfile
├── docker-compose.yml
├── run_api.py
├── run_m5_eval.py
└── pyproject.toml
```

## Key design decisions

### Deterministic analytics first
Critical filtering, ranking, aggregation, risk scoring and scenario calculations are Python functions with structured schemas. The model selects and explains tools rather than owning numerical logic.

### RAG is a tool, not the whole application
Policy retrieval complements structured service evidence; it is not a standalone document chatbot.

### National threshold invariant
Scenario percentiles are always calculated from the national validated Centre-Based Care risk sample. State/urban-rural filters change the reported population, not the meaning of P80 or P25.

### Product mode vs strict grounding
The API defaults to product mode so legitimate no-tool boundary answers such as “the dataset has no waitlist data” can be returned. Set `strict_grounding=true` on `/api/chat` when a caller wants every accepted response to contain deterministic tool evidence.

### Evaluation is part of the system
M5 stores raw reports and machine-readable metrics, allowing failures to be re-scored without new API calls. The product system-info endpoint exposes the latest completed 50-case evaluation snapshot.

## Limitations

- the risk model was derived for this portfolio/academic dataset and is not a production regulatory model
- the v1 risk score is scoped to Centre-Based Care
- policy retrieval uses a versioned Guide snapshot and can become stale until the corpus is refreshed
- authorised capacity does not measure demand, enrolment, utilisation, vacancies or waiting lists
- BM25 retrieval is intentionally simple and auditable; semantic reranking may improve recall in a larger corpus
- the frontend is designed for portfolio demonstration, not multi-user production operation
- there is no authentication, persistence or role-based access control in v0.6

## Portfolio framing

**AI PM:** problem definition → analyst workflow → task-oriented Agent → scenario exploration → trust boundaries → measurable evaluation.

**FDE:** data contracts → deterministic tools → LLM orchestration → grounded RAG → scenario engine → tracing/evals → HTTP API → containerised delivery.

## Documentation

- `docs/ARCHITECTURE.md`
- `docs/EVALUATION.md`
- `docs/MILESTONE_6.md`
- `docs/DEPLOYMENT.md`
- `docs/DESIGN_DECISIONS.md`
