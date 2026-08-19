# Design decisions — v0.1

## 1. Retrieval scope and risk scope are separate

A natural-language filter such as `QLD + Rural + Centre-Based Care` finds **227** rows in the cleaned dataset. Only **193** of those satisfy the notebook's stricter validated risk-analysis requirements (valid spatial data, successful SOS classification, usable transport distance, usable NQS rating, and non-missing approved places).

This distinction is intentional:

- `search_services` answers **what records exist?**
- risk tools answer **what can be validly scored under the current model?**

The Agent must not silently present 193 as the total number of QLD rural CBC services.

## 2. Thresholds are globally stable in v0.1

The notebook calculated risk thresholds on the national eligible Centre-Based Care sample:

- poor access threshold = P75 nearest public transport distance = ~5.329 km
- low capacity threshold = P25 approved places = 40

A user filter such as `state=QLD` does not recompute these thresholds. This keeps the risk definition stable across queries and makes evaluations reproducible.

## 3. `gap_score` is a screening signal, not causal risk

The score is the sum of three observed disadvantage flags:

- poor transport access
- Below Meeting NQS quality
- low authorised capacity

It does not prove why a service has a given outcome, and it does not prove unmet demand.

## 4. Ranking has no hidden weights

For `find_high_risk_services`, v0.1 ranks by:

1. gap score descending
2. nearest public transport distance descending
3. approved places ascending
4. service approval number ascending

This is deliberately simple and inspectable. Scenario-specific weights can be added later as an explicit product feature rather than hidden in a prompt.

## 5. Policy retrieval is a separate evidence layer in v0.3

The service dataset answers what is observed in the QBUS6860-derived data. ACECQA/NQF retrieval answers what official guidance says. The model does not merge those sources into a new score.

A combined regulatory-prioritisation question should therefore produce two traceable tool paths rather than one opaque LLM judgement.

## 6. Curated allow-list before open web search

The first policy corpus is intentionally restricted to official ACECQA pages selected for product relevance. This improves provenance, refreshability and evaluation. Open-web retrieval is not part of the Agent runtime.

## 7. BM25 before embeddings

The v0.3 corpus is small enough that an in-memory BM25 index is a reasonable first retrieval baseline. It adds no embedding cost or vector-store operational dependency. Semantic reranking should only be added if retrieval evals show a meaningful recall gap.

## 8. Policy citations are validated application-side

The LLM may reference only `chunk_id` values returned by `search_policy` in the same run. URLs and source metadata exposed to the user are resolved from tool output rather than trusted from model-generated text.

## 9. Regulatory prioritisation is not enforcement

The v1 risk score identifies overlapping disadvantage signals and can support prioritisation for analyst attention. It is not evidence of non-compliance and does not automatically justify a compliance notice or another enforcement tool.

The Agent must also distinguish ACECQA from the state/territory regulatory authorities responsible for administering, assessing/rating and monitoring/enforcing under the NQF.
