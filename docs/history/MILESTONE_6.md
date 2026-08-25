# Milestone 6 — Productisation and Deployment

## Goal

Turn the evaluated command-line Agent into a reproducible portfolio product without changing the nine M1–M4 product tools or the M5 benchmark logic.

## Scope

M6 adds four delivery surfaces:

1. **FastAPI API** for Agent chat and deterministic endpoints.
2. **Browser demo** served by the same API process.
3. **Docker / Compose packaging** for reproducible local delivery.
4. **Portfolio documentation** that presents the problem, architecture, reliability design and formal evaluation results.

## API endpoints

- `GET /health`
- `GET /api/system/info`
- `POST /api/chat`
- `GET /api/services/{service_approval_number}`
- `POST /api/scenario`
- `POST /api/policy/search`

The API exposes full Agent evidence, resolved policy sources, usage/latency telemetry and tool trace. Deterministic service/scenario/policy endpoints can be demonstrated without an LLM call.

## Frontend

The frontend is deliberately lightweight HTML/CSS/JavaScript rather than a second Python/Node application. It includes:

- Copilot prompt input
- example prompts
- strict-grounding toggle
- answer/evidence/policy panels
- tool badges and trace
- usage/latency telemetry
- Scenario Lab
- service lookup
- live M5 evaluation snapshot

Model text is inserted using text nodes, not as model-generated HTML.

## Grounding behaviour

M5 evaluation retains strict per-case settings. The product `/api/chat` endpoint defaults to `strict_grounding=false` so legitimate no-tool boundary answers can be returned. When strict mode is requested, the existing runtime grounding validator rejects no-tool responses.

A successful product-mode no-tool answer is explicitly labelled `boundary_no_tool`; a response using tools is labelled `tool_grounded`.

## Zero-token acceptance

```bash
pytest -q
python scripts/check_m5_benchmark.py
python scripts/check_policy_corpus.py
python scripts/check_m6_product.py
```

Expected:

```text
42 passed
M5 benchmark integrity: PASS (50 cases)
Corpus integrity: PASS
M6 product integrity: PASS
```

## Local HTTP acceptance

```bash
python run_api.py
```

Then verify:

- `/health` returns HTTP 200
- `/` renders the product demo
- `/docs` renders OpenAPI docs
- Scenario Lab returns baseline 162 and P80/P25 149
- Service `SE-40000427` resolves to Napranum Early Childhood Centre
- one Agent prompt returns tool-grounded evidence with an API key configured

## Docker acceptance

```bash
cp .env.example .env
# set OPENAI_API_KEY
docker compose up --build
```

Then repeat the HTTP acceptance checks at `http://localhost:8000`.

## Definition of Done

M6 is ready to freeze when:

- M1–M5 regressions remain green
- FastAPI zero-token endpoints pass
- browser frontend loads
- one live Agent query succeeds through `/api/chat`
- Docker image builds and the Compose service passes `/health`
- README reflects the completed M5 benchmark and the actual product architecture

## Non-goals

M6 does not add:

- Multi-Agent orchestration
- Memory
- MCP
- authentication / user accounts
- persistent chat storage
- production-grade cloud infrastructure

Those are optional follow-ons only if they improve the hiring narrative or a real deployment requirement appears.
