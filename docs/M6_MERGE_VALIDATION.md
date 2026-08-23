# M6 Merge Validation

## Baseline

Milestone 6 was merged directly into the user-provided M5.1 repository archive. No older assistant-side repository was used as the product baseline.

Before M6 changes:

```text
36 passed
```

The repository already contained the completed M5 v1.1 result:

```text
50/50 passed
Task Success Rate 100%
Critical cases PASS
M5 ready YES
```

## M6 additions

- `src/acecqa_agent/api/`
- `frontend/`
- `run_api.py`
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `.env.example`
- `tests/test_api.py`
- `scripts/check_m6_product.py`
- `.github/workflows/ci.yml`
- `Makefile`
- `docs/MILESTONE_6.md`
- `docs/DEPLOYMENT.md`

Updated:

- `pyproject.toml` -> v0.6.0 + product dependencies
- `requirements.txt`
- `src/acecqa_agent/__init__.py`
- `README.md`
- `docs/ARCHITECTURE.md`

## Regression validation

After the merge:

```text
42 passed
M5 benchmark integrity: PASS (50 cases)
Corpus integrity: PASS (1395 chunks)
M6 product integrity: PASS
JS syntax: PASS
Python compile: PASS
```

`check_m6_product.py` verifies:

- `/health`
- `/api/system/info`
- 17,663 service records
- 1,395 policy chunks
- nine tools
- completed 50/50 M5 snapshot
- deterministic P80/P25 regression: 162 -> 149 (-13)

## Local HTTP validation

Uvicorn was started against the merged repository and verified:

```text
GET /health -> 200
GET / -> product HTML loaded
```

## Environment limitation

Docker CLI was not available in the build environment used for this merge. Dockerfile and Compose files are included, but the final container build/health acceptance must be run on a machine with Docker installed.
