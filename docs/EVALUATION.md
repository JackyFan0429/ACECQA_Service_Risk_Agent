# Evaluation Design

## Why a separate formal benchmark?

M2, M3 and M4 smoke tests were development acceptance tests. They answered whether each newly introduced capability worked on a small set of milestone-specific examples.

M5 is different: it evaluates the **complete system after feature freeze** on one fixed 50-case benchmark.

## Evaluation boundary

The Agent remains responsible for:

- understanding natural-language intent;
- selecting tools;
- mapping user language into tool parameters;
- composing evidence into a useful answer;
- expressing uncertainty and analytical limitations.

Python tools remain responsible for:

- filtering and counts;
- risk scores and rankings;
- comparisons and quartile summaries;
- scenario calculations.

The local policy retriever remains responsible for returning official ACECQA/NQF chunks.

Therefore the evaluator should inspect those boundaries directly rather than asking another LLM whether an answer "looks good".

## Benchmark schema

Each case may define:

- `tool_expectation`
  - `exact`
  - `contains`
  - `none`
  - `allowed_subset`
  - `any_of`
  - optional `max_calls` for routing-efficiency checks
- `argument_checks`
- `output_checks`
- `answer_checks`
- `evidence_tools`
- `policy_checks`
- `run.require_tool`
- `critical`

### Path syntax

Structured checks use a small JSONPath-like syntax:

```text
data.services[0].service_approval_number
data.groups[group=Rural].median_nearest_transport_km
data.quartiles[transport_access_quartile=Q4 Farthest].below_meeting_rate
```

Supported comparisons include exact equality, approximate numerical matching with tolerance, membership, substring containment, existence and numerical inequalities.

## Why lightweight text checks remain

Some reliability claims are semantic rather than numerical:

- approved capacity does not prove unmet demand;
- Working Towards NQS does not itself prove unsafe care;
- a triple-gap score is not a legal breach finding;
- a smaller scenario pool does not prove a better policy;
- Guide material does not override the National Law/Regulations.

For these cases M5 checks broad phrase groups and forbidden claims. It intentionally avoids demanding one exact sentence.

## Policy grounding

A policy case passes grounding only when the runtime resolves cited chunk IDs to real `policy_sources`. The evaluator can require:

- at least one resolved source;
- source URL host ending in `acecqa.gov.au`;
- an allowed authority level.

This is stronger than trusting model-written source names or URLs.

## Reproducibility

The deterministic dataset and policy corpus are versioned local project assets. M5 output expectations are regression-tested against the deterministic tools before live evaluation.

Run:

```bash
python scripts/check_m5_benchmark.py
pytest -q
```

before spending API tokens.

## Interpretation

A high M5 score demonstrates reliability on this fixed benchmark and data/policy snapshot. It does not prove:

- causal relationships;
- policy optimality;
- legal compliance or non-compliance;
- suitability for autonomous enforcement decisions;
- performance on every possible user query.

The product remains decision support for human analysts/regulators.
