# ACECQA Service Risk Copilot

AI-agent project evolved from QBUS6860 spatial/data analysis. The current milestone extracts validated notebook logic into deterministic, typed Python tools so an LLM can orchestrate analysis without inventing calculations.

## Current milestone: deterministic tool layer

The repository currently implements six tools:

1. `search_services`
2. `get_service_profile`
3. `calculate_risk_score`
4. `find_high_risk_services`
5. `compare_transport_access`
6. `analyse_transport_quartile_outcomes`

The original notebook is retained in `notebooks/` for provenance. `data/education_services_cleaned.csv` contains 17,663 service records. Retrieval tools can search the full cleaned dataset; risk tools apply the stricter validated analysis scope from the notebook.

## Preserved risk definition

For the validated Centre-Based Care analysis scope:

- poor transport access: nearest public transport distance >= national P75
- weak quality: overall NQS rating below Meeting NQS
- low authorised capacity: approved places <= national P25
- gap score: sum of those three binary flags (0–3)

From the supplied notebook data, the preserved thresholds are approximately:

- P75 transport distance: 5.329 km
- P25 approved places: 40
- triple-gap services nationally: 162

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
python demo_tools.py
pytest -q
```

## Repository structure

```text
acecqa-risk-agent/
├── data/
│   └── education_services_cleaned.csv
├── notebooks/
│   └── QBUS6860_A1.ipynb
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DESIGN_DECISIONS.md
│   ├── TOOL_SCHEMAS.md
│   └── tool_schemas.json
├── src/acecqa_agent/
│   ├── config.py
│   ├── data_repository.py
│   ├── schemas.py
│   ├── agent/
│   │   ├── system_prompt.py
│   │   └── tool_registry.py
│   └── tools/
│       ├── common.py
│       ├── service_search.py
│       ├── risk_analysis.py
│       └── comparison.py
├── tests/
│   └── test_tools.py
├── examples/
│   └── qld_rural_top20.json
├── demo_tools.py
├── scripts_generate_schemas.py
├── pyproject.toml
└── requirements.txt
```

## Next milestone

Add a **single-agent orchestration layer** that can turn:

> Find the highest-risk rural Centre-Based Care services in Queensland.

into the correct tool call(s), then generate an evidence-grounded explanation. Policy RAG, scenario analysis, evals, API/Docker, and MCP come later.
