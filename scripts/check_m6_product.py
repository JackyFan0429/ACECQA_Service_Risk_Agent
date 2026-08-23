"""Zero-token Milestone 6 product integrity check."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from acecqa_agent.api.main import app


def main() -> None:
    client = TestClient(app)
    checks = []

    health = client.get("/health")
    checks.append(("health", health.status_code == 200 and health.json().get("status") == "ok"))

    info = client.get("/api/system/info")
    payload = info.json() if info.status_code == 200 else {}
    checks.append(("system_info", info.status_code == 200))
    checks.append(("service_records", payload.get("service_records") == 17663))
    checks.append(("policy_chunks", payload.get("policy_chunks") == 1395))
    checks.append(("tool_count", payload.get("tool_count") == 9))
    checks.append(("m5_snapshot", (payload.get("evaluation") or {}).get("passed") == 50))

    scenario = client.post(
        "/api/scenario",
        json={"transport_percentile": 0.80, "capacity_percentile": 0.25},
    )
    result = (scenario.json().get("result") or {}) if scenario.status_code == 200 else {}
    checks.append(("scenario_162_to_149", (
        (result.get("baseline") or {}).get("priority_service_count") == 162
        and (result.get("scenario") or {}).get("priority_service_count") == 149
        and result.get("change_count") == -13
    )))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if failed:
        raise SystemExit("M6 product integrity: FAIL -> " + ", ".join(failed))
    print("M6 product integrity: PASS")


if __name__ == "__main__":
    main()
