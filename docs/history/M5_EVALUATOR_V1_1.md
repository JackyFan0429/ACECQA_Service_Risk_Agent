# Milestone 5 evaluator / boundary patch v1.1

This patch is based on the first 50-case formal run and makes one Agent behaviour fix plus three scoring-rubric corrections.

## Why v1.1 exists

The first formal run produced four failing cases. Raw-report review showed:

- **M5-P07** — answer, tool identity and policy grounding were correct. The Agent refined a weak first BM25 retrieval with a second `search_policy` query. v1.1 allows one retrieval refinement for this case; repeated retrieval remains visible in token/tool-call efficiency metrics.
- **M5-B02** — false negative caused by `can’t` (curly apostrophe) versus the evaluator marker `cannot`. Text normalisation now canonicalises common contractions.
- **M5-B10** — false negative caused by the valid phrase `No profile was found`. Equivalent unknown-service wording is now accepted.
- **M5-B09** — genuine Agent behaviour issue. The Agent correctly rejected subgroup-specific percentile recomputation but stopped before running the nearest valid scenario. The system prompt now requires `simulate_risk_thresholds(state="QLD", urban_rural="Rural", transport_percentile=0.80, capacity_percentile=0.25)` and an explicit explanation that P80 remains nationally defined.

The 50 benchmark **queries are unchanged**. Benchmark rubric version is bumped from 1.0 to 1.1 for reproducibility.

## Minimal rerun

After applying the patch, do not spend tokens rerunning all 50 cases. In the original full-run directory run:

```bash
python run_m5_eval.py \
  --resume evals/m5_results/<YOUR_RUN_DIR> \
  --retry-errors
```

Only M5-B09 had a saved `run_error`, so this should make one live API rerun and reuse the other 49 raw reports.

Then run:

```bash
python recheck_m5_results.py evals/m5_results/<YOUR_RUN_DIR>
```

The recheck uses 0 API tokens and scores all 50 raw reports with benchmark/evaluator v1.1.
