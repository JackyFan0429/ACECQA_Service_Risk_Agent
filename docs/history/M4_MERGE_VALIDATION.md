# Milestone 4 merge validation

Milestone 4 was merged directly onto the supplied working Milestone 3 repository.

## Preserved M3 assets

- cleaned service dataset
- official July 2026 Guide to the NQF PDF
- generated 1,395-chunk policy corpus
- corpus manifest and source configuration
- Milestone 3 ingestion/check scripts
- Milestone 3 smoke-test cases and saved results
- policy retrieval implementation and grounding runtime

## Added M4 capability

- `simulate_risk_thresholds`
- `compare_risk_scenarios`
- scenario Pydantic input/output schemas
- agent routing rules for Pxx percentile language and A/B scenario requests
- deterministic scenario demos
- Milestone 4 smoke-test runner and benchmark cases

## Validation performed after merge

- `pytest -q` -> **25 passed**
- policy corpus integrity -> **PASS**
- policy chunks -> **1,395**
- registered tools -> **9**
- national baseline P75/P25 -> **162** priority services
- national P80/P25 -> **149** priority services
- change -> **-13**
- national P80 transport cutoff -> **6.744341249608515 km**
- QLD Rural risk-eligible services -> **193**
- QLD Rural baseline -> **21**
- QLD Rural P80/P25 -> **20**

No live OpenAI API smoke test was executed during this merge. Run `run_m4_smoke_tests.py` locally with your API key for Milestone 4 live acceptance.
