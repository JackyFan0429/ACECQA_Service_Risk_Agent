# Documentation map

This folder separates **current engineering documentation** from historical milestone notes.

## Start here

- [Architecture](ARCHITECTURE.md) — system boundaries, product surface, tool layers and evaluation plane.
- [Design Decisions](DESIGN_DECISIONS.md) — why the project uses deterministic analytics, a single agent, local BM25 RAG and explicit trust boundaries.
- [Evaluation](EVALUATION.md) — the 50-query benchmark, scoring dimensions, trace-based checks and reproducibility model.
- [Deployment](DEPLOYMENT.md) — local Python and Docker Compose operation.

## Capability references

- [Tool Schemas](TOOL_SCHEMAS.md) — the nine product tool contracts.
- [Scenario Analysis](SCENARIO_ANALYSIS.md) — threshold invariants and deterministic sensitivity analysis.
- [Policy Corpus](POLICY_CORPUS.md) — policy source hierarchy, ingestion and citation integrity.
- [PDF Ingestion](M3_PDF_INGESTION.md) — current PDF-based corpus refresh workflow.

## Historical development record

Milestone definitions, install notes, evaluator patches and merge validation documents are retained under [`history/`](history/). They are useful for understanding the development path, but are not required to run the current frozen product.
