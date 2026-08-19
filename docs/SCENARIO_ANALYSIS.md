# Scenario analysis design

## Why this is a separate deterministic layer

The product question is not only “which services are high priority now?” but also “how sensitive is that priority list to the assumptions?”

The LLM therefore orchestrates scenario tools but never performs threshold arithmetic itself.

```text
User assumption
    ↓
Single Agent
    ↓
simulate_risk_thresholds / compare_risk_scenarios
    ↓
National validated CBC sample
    ↓
percentile cut-offs + new flags + priority membership
    ↓
structured scenario result
    ↓
LLM explanation
```

## Model invariants

1. Risk scope remains Centre-Based Care only.
2. Weak-quality definition remains the existing below-Meeting-NQS binary rule.
3. Transport threshold uses a percentile of national valid CBC transport distance.
4. Capacity threshold uses a percentile of national valid CBC authorised places.
5. Percentiles are supplied as decimals (`0.80 = P80`).
6. Subgroup filters never redefine thresholds.
7. Scenario results do not overwrite the validated default risk model.

## Output design

Both tools expose decision-relevant fields rather than just a final count:

- numerical threshold values
- eligible population
- priority count and rate
- absolute and percentage change
- overlap / entering / leaving counts
- changed-service samples
- by-state impact
- by-urban/rural impact
- interpretation caveat

This lets the LLM explain trade-offs without recomputing business-critical numbers.
