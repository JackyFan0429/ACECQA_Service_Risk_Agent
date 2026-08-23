# M6.1 Docker Policy Path fix

This fixes the Docker-only `GET / -> 404 Not Found` and Docker-only policy corpus lookup failures where `policy_repository.py`
was deriving the repository root from its installed `site-packages` path.

The policy repository now uses the shared `PROJECT_ROOT` contract from
`acecqa_agent.config`, which resolves to `/app` in Docker via
`ACECQA_PROJECT_ROOT=/app`.

Cause: the non-editable package install puts `acecqa_agent/config.py` under `site-packages`, so the old `PROJECT_ROOT = Path(__file__).resolve().parents[2]` no longer points at `/app`. As a result `/app/frontend`, `/app/data`, and `/app/evals` are not discovered through `PROJECT_ROOT`.

Fix:
- `Dockerfile` sets `ACECQA_PROJECT_ROOT=/app`.
- `src/acecqa_agent/config.py` honours that environment variable while preserving the old local editable-install fallback.

After copying these files into the project root:

```bash
docker compose down
docker compose build --no-cache
docker compose up
```

Then verify:

```bash
curl http://localhost:8000/health
curl -I http://localhost:8000/
```

Expected Docker checks after rebuild:

- `/` -> 200
- `/health` -> 200
- `/api/system/info` -> 200
- policy chunks -> 1395
- service records -> 17663
- M5 evaluation -> 50/50 ready

