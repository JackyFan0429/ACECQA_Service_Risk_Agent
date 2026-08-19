# Milestone 2 Behaviour Smoke Test

This suite validates the live Single Agent before Milestone 3 (Policy RAG).

## Why `python demo_agent.py "..." --show-trace` failed

`"..."` is not a placeholder to the shell. It is passed literally to the Agent as the user's query.
Because three dots do not require ACECQA data, the Agent may produce a no-tool response, and the normal
`demo_agent.py` runtime correctly rejects that response as ungrounded.

Use a real query, for example:

```bash
python demo_agent.py \
  "Find the highest-risk rural Centre-Based Care services in Queensland." \
  --show-trace
```

## Files

- `evals/smoke_cases.json` — the 12 acceptance cases and expected routing/parameters.
- `run_smoke_tests.py` — runs the live Agent and scores the cases.
- `evals/results/` — generated run reports. Each run gets its own timestamped folder.

## Step 1 — Activate the same environment

From the project root:

```bash
source .venv/bin/activate
```

Check the key exists in this shell:

```bash
python -c "import os; print('OPENAI_API_KEY set:', bool(os.getenv('OPENAI_API_KEY')))"
```

Expected:

```text
OPENAI_API_KEY set: True
```

If it is `False`, export the key again in this Terminal session.

## Step 2 — Confirm the 12 cases without spending API tokens

```bash
python run_smoke_tests.py --list
```

This should print M2-01 through M2-12.

## Step 3 — Run one cheap sanity case first

```bash
python run_smoke_tests.py --case M2-03
```

M2-03 is critical because it checks that a simple population count uses `search_services`, not the stricter risk-ranking tool.
The expected answer is 227 Queensland rural Centre-Based Care services.

A partial run does not issue an overall Milestone 2 verdict.

## Step 4 — Run the complete suite

```bash
python run_smoke_tests.py
```

Optional: add a short pause between requests if you hit rate limits:

```bash
python run_smoke_tests.py --pause 1
```

The runner continues after an individual case failure instead of stopping the whole suite.

## Step 5 — Read the final verdict

At the end you will see something like:

```text
Passed: 12/12
Summary: evals/results/20260819_XXXXXX/summary.md
JSON:    evals/results/20260819_XXXXXX/summary.json
Milestone 2 ready: YES
```

The acceptance rule is:

- at least **11/12** total cases pass; and
- all four critical cases pass: **M2-03, M2-09, M2-10, M2-12**.

For the three semantic boundary cases M2-09, M2-10 and M2-12, also read their raw JSON answers before freezing v0.2. The automated answer checks are intentionally lightweight and should not replace a quick human review.

## What the critical cases mean

- **M2-03 — Search vs risk scope:** must use `search_services` and return the full filtered population, not the risk-eligible subset.
- **M2-09 — Capacity ≠ demand:** must not infer unmet demand from authorised capacity. No tool call is expected.
- **M2-10 — Family Day Care unsupported:** must not silently apply the Centre-Based Care risk model. Either a direct scope refusal or `find_high_risk_services` returning its scope error is accepted.
- **M2-12 — Waitlist hallucination:** must state that the current data do not establish waiting-list status. No tool call is expected.

## Useful targeted commands

Run only the four critical cases:

```bash
python run_smoke_tests.py --critical-only
```

Run two named cases:

```bash
python run_smoke_tests.py --case M2-03 --case M2-12
```

Override the model:

```bash
python run_smoke_tests.py --model "$ACECQA_AGENT_MODEL"
```

## What to send back for review

After the full run, send:

1. the generated `summary.md`; and
2. if any case fails, the corresponding `M2-XX_raw.json` file(s).

That is enough to decide whether to freeze Milestone 2 or make one targeted prompt/tool fix before starting Policy RAG.
