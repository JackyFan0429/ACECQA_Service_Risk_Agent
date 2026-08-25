# Milestone 4 — Mac installation and acceptance

Apply the Milestone 4 patch to your existing v0.3 project, then run:

```bash
cd /Users/jackymini/Downloads/acecqa-risk-agent02
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

Expected offline result:

```text
25 passed
```

## 1. Verify deterministic scenario analysis without API tokens

```bash
python demo_scenario.py --transport 0.80 --capacity 0.25
```

Key expected values:

```text
baseline.priority_service_count = 162
scenario.priority_service_count = 149
change_count = -13
scenario transport cutoff ≈ 6.744341 km
```

QLD Rural:

```bash
python demo_scenario.py \
  --transport 0.80 \
  --capacity 0.25 \
  --state QLD \
  --urban-rural Rural
```

Expected:

```text
eligible = 193
baseline priority = 21
scenario priority = 20
```

## 2. Live Single-Agent test

```bash
python demo_agent.py \
  "If poor transport changes from P75 to P80 while capacity stays P25, how does the national triple-gap priority pool change?" \
  --show-trace
```

Expected routing:

```text
simulate_risk_thresholds
transport_percentile = 0.80
capacity_percentile = 0.25
minimum_gap_score = 3
```

## 3. Compare two scenarios

```bash
python demo_agent.py \
  "Compare a broad triple-gap scenario at P70 transport/P30 capacity with a strict scenario at P85/P20." \
  --show-trace
```

Expected routing: `compare_risk_scenarios`.

## 4. Smoke tests

List cases without API use:

```bash
python run_m4_smoke_tests.py --list
```

Run one critical case first:

```bash
python run_m4_smoke_tests.py --case M4-02
```

Then:

```bash
python run_m4_smoke_tests.py --pause 1
```

Upload the newest `evals/m4_results/<timestamp>/summary.md`. If any case fails, also upload that case's `_raw.json` file.
