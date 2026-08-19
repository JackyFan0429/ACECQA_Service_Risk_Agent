# M5 Merge Validation

## Baseline

Milestone 5 was merged directly into the user-provided `acecqa-risk-agent-M4.zip` repository. The M4 repository is the source of truth; M5 does not replace it with an older template.

## Preserved M4 assets

The merge preserves:

- `data/education_services_cleaned.csv`
- the existing local policy corpus and manifest
- the versioned official Guide PDF
- all nine M4 product tools
- M2/M3/M4 smoke-test assets and historical result folders
- existing Agent runtime, grounding validation and policy retrieval logic
- scenario-analysis implementation and regression behaviour

## M5 additions

### Formal benchmark

- `evals/m5_benchmark.json` — 50 fixed benchmark cases
- `evals/m5_benchmark.schema.json` — benchmark format reference
- `evals/m5_results/.gitkeep`

### Evaluation runtime

- `src/acecqa_agent/evals/m5_harness.py`
- `src/acecqa_agent/evals/__init__.py`
- `run_m5_eval.py`
- `recheck_m5_results.py`
- `scripts/check_m5_benchmark.py`

### Tests and documentation

- `tests/test_m5_harness.py`
- `docs/MILESTONE_5.md`
- `docs/MILESTONE_5_INSTALL.md`
- `docs/EVALUATION.md`
- `docs/M5_MERGE_VALIDATION.md`

### Version/documentation updates

- package version -> `0.5.0`
- README -> formal evaluation workflow
- architecture -> M5 evaluation plane

## Offline validation performed after merge

```text
pytest -q
32 passed

python scripts/check_m5_benchmark.py
M5 benchmark integrity: PASS (50 cases)
- data_retrieval: 8
- risk_analysis: 8
- comparison: 6
- policy_rag: 8
- scenario_analysis: 8
- reliability_boundary: 12

python scripts/check_policy_corpus.py
Chunks: 1395
Sources: 1
Corpus integrity: PASS
```

Scenario regression was also rechecked:

```text
baseline P75/P25 = 162
P80/P25 = 149
change = -13
P80 transport cutoff = 6.744341249608515 km
```

## Deterministic benchmark lock

`tests/test_m5_harness.py` invokes the real deterministic tools against all M5 structured output expectations. This prevents the benchmark JSON from silently drifting away from the actual M4 analytics/scenario layer.

The benchmark currently contains:

- 84 explicit tool-argument checks
- 80 structured deterministic output checks
- 12 policy-grounding cases
- 12 reliability/boundary cases

## No live M5 claim yet

The merged repository is **M5 code-ready**, not M5-passed. A live 50-case benchmark still needs to be run with the user's API key. Only that live result should be used to claim final Task Success / Tool Selection / Parameter / Grounding metrics.
