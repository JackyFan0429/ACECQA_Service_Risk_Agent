# Evaluation assets

This directory contains the development smoke suites and the formal benchmark used to evaluate the frozen product.

## Formal benchmark

- `m5_benchmark.json` — fixed 50-query benchmark (v1.1)
- `m5_benchmark.schema.json` — benchmark schema
- `m5_results/20260819_221712/` — retained complete 50/50 final run, including raw case reports, metrics and run configuration

The final benchmark covers:

- data retrieval: 8 cases
- risk analysis: 8 cases
- comparison: 6 cases
- policy RAG: 8 cases
- scenario analysis: 8 cases
- reliability / boundary handling: 12 cases

The formal evaluator prioritises deterministic tool trace, arguments and structured outputs over brittle answer-string matching. A benchmark pass demonstrates behaviour on this fixed test set; it is not proof of regulatory validity or real-world policy optimality.

## Earlier milestone suites

- `m3_cases.json` — policy-grounded agent acceptance suite
- `m4_cases.json` — scenario-analysis acceptance suite
- `smoke_cases.json` — earlier single-agent behaviour suite

Only the final successful M3, M4 and M5 result snapshots are retained in the cleaned portfolio repository.
