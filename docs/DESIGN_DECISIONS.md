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
