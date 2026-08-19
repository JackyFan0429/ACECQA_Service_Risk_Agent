# Tool schemas — v0.1

## 1. `search_services`
**Purpose:** deterministic filtering / retrieval across the cleaned dataset. This does not imply every returned row is eligible for risk scoring.

Input:
```json
{
  "state": "QLD",
  "urban_rural": "Rural",
  "service_type": "Centre-Based Care",
  "overall_rating": null,
  "limit": 20
}
```
Output:
```json
{
  "matched_count": 227,
  "returned_count": 20,
  "filters": {},
  "services": [{"service_approval_number": "...", "service_name": "..."}]
}
```

## 2. `get_service_profile`
**Purpose:** fetch decision-relevant facts for exactly one service.

Input:
```json
{"service_approval_number": "SE-40000427"}
```
Output includes provider, location, urban/rural class, rating, approved places, train/bus/nearest-transport distance, and coordinates.

## 3. `calculate_risk_score`
**Purpose:** reproduce the assignment's 3-gap risk definition for one eligible CBC service.

Input:
```json
{"service_approval_number": "SE-40000427"}
```
Output:
```json
{
  "eligible_for_risk_scoring": true,
  "gap_score": 3,
  "poor_access_flag": true,
  "weak_quality_flag": true,
  "low_capacity_flag": true,
  "thresholds": {
    "transport_p75_km": 5.329340006807538,
    "capacity_p25_places": 40.0
  },
  "limitations": ["Approved places ... not ... unmet demand."]
}
```

## 4. `find_high_risk_services`
**Purpose:** produce a reproducible priority list.

Input:
```json
{
  "state": "QLD",
  "urban_rural": "Rural",
  "service_type": "Centre-Based Care",
  "minimum_gap_score": 2,
  "top_k": 20
}
```
Ranking rule:
1. gap score descending;
2. nearest public transport distance descending;
3. approved places ascending;
4. service approval number ascending.

This rule is intentionally explicit and contains no hidden LLM weighting.

## 5. `compare_transport_access`
**Purpose:** compare access statistics by `urban_rural`, `state`, or `service_type`.

Input:
```json
{"state": "QLD", "service_type": "Centre-Based Care", "group_by": "urban_rural"}
```
Output per group: count, median, mean, and P75 nearest-public-transport distance.

## 6. `analyse_transport_quartile_outcomes`
**Purpose:** combine the notebook's quality-vs-access and capacity-vs-access views into one tool.

Input:
```json
{
  "state": "QLD",
  "urban_rural": "Rural",
  "service_type": "Centre-Based Care",
  "min_group_size": 20
}
```
Output per national transport-access quartile: service count, Below Meeting NQS rate, capacity non-missing count, median approved places, and mean approved places.

**Important:** this tool does not infer demand from approved capacity.
