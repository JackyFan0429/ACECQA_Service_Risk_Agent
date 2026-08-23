# Deployment Guide — v0.6

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
export OPENAI_API_KEY="your-key"
python run_api.py
```

Environment variables:

- `OPENAI_API_KEY` — required only for `/api/chat`
- `ACECQA_AGENT_MODEL` — optional model override; defaults to the runtime model setting
- `PORT` — local `run_api.py` port; defaults to `8000`
- `ACECQA_HOST` — defaults to `0.0.0.0`
- `ACECQA_RELOAD=1` — optional local reload mode
- `ACECQA_POLICY_CORPUS_PATH` — optional policy corpus override

## Docker Compose

```bash
cp .env.example .env
# edit .env
docker compose up --build
```

The container exposes port 8000 and includes a Docker healthcheck against `/health`.

## Why one container?

The frontend is static and served by FastAPI. A second frontend process would add deployment complexity without demonstrating additional Agent/product capability. A single container is easier for an interviewer or reviewer to reproduce.

## Production gaps

Before a real multi-user deployment, add at minimum:

- API authentication and rate limiting
- secret management rather than local `.env`
- structured logging / central observability
- request IDs
- persistent audit storage where required
- concurrency/load testing
- policy-corpus refresh/version workflow
- deployment-specific HTTPS and network controls
- legal/regulatory review of the risk model and user-facing claims
