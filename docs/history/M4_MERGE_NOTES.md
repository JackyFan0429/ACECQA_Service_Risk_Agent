# Milestone 4 merge notes

This v0.4 repository was merged directly onto the user's working Milestone 3 repository.

Preserved unchanged from the supplied M3 base:

- `data/education_services_cleaned.csv`
- `data/policy/policy_chunks.jsonl`
- `data/policy/corpus_manifest.json`
- `data/policy/raw/guide_to_nqf_2026_07.pdf`
- `data/policy/sources.json`
- PDF ingestion/check scripts
- Milestone 2/3 smoke-test scripts and saved project docs
- Policy retrieval implementation and corpus

Added/updated for Milestone 4:

- `src/acecqa_agent/tools/scenario_analysis.py`
- scenario Pydantic schemas
- two scenario tools in the agent registry/adapter
- Milestone 4 routing rules in the system prompt
- runtime data-tool allow-list updated to include scenario tools
- `demo_scenario.py`
- `run_m4_smoke_tests.py`
- `evals/m4_cases.json`
- scenario tests and docs

The validated default risk model is not overwritten by scenario analysis. Scenario thresholds are hypothetical and are always computed from the same national validated Centre-Based Care sample.
