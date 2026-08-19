# M5 v1.1 evaluator + boundary patch

Apply this patch on top of the M5 project that produced the 46/50 formal run.

Changes:
- evaluator normalises curly apostrophes/common contractions;
- M5-P07 allows one refined `search_policy` retry (same correct tool); repeated search remains visible in efficiency metrics;
- M5-B10 accepts equivalent unknown-service wording such as `No profile was found`;
- M5-B09 system prompt now runs the nearest valid national-threshold scenario with QLD/Rural filters instead of stopping at refusal;
- grounding failures retain partial run answer/trace/usage for accurate eval diagnostics;
- benchmark rubric version is 1.1; the 50 user queries are unchanged.

After copying the patch into your project, run:

```bash
pytest -q
python scripts/check_m5_benchmark.py
```

Then reuse the original full-run directory and rerun only runtime errors:

```bash
python run_m5_eval.py \
  --resume evals/m5_results/<ORIGINAL_RUN_DIR> \
  --retry-errors
```

Because the original run had only M5-B09 as `run_error`, the other 49 raw reports are reused and only B09 should call the API again.

Finally re-score all 50 cases at 0 API tokens:

```bash
python recheck_m5_results.py evals/m5_results/<ORIGINAL_RUN_DIR>
```

Inspect `summary_rechecked.md` and `evaluation_report_rechecked.md`.
