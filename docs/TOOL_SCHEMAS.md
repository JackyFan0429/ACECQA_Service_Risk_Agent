# Tool Schemas

The exact machine-readable schemas are generated from Pydantic models into `docs/tool_schemas.json`.

## 1. `search_services`

Deterministic filtering/count/listing across the cleaned dataset. It does not imply every returned row is eligible for risk scoring.

```json
{
  "state": "QLD",
  "urban_rural": "Rural",
  "service_type": "Centre-Based Care",
  "overall_rating": null,
  "limit": 20
}
```

## 2. `get_service_profile`

Fetch decision-relevant facts for one exact service approval number.

```json
{"service_approval_number": "SE-40000427"}
```

## 3. `calculate_risk_score`

Reproduce the validated v1 0–3 gap score for one eligible Centre-Based Care service.

```json
{"service_approval_number": "SE-40000427"}
```

## 4. `find_high_risk_services`

Produce a reproducible priority list with no hidden LLM weighting.

```json
{
  "state": "QLD",
  "urban_rural": "Rural",
  "service_type": "Centre-Based Care",
  "minimum_gap_score": 3,
  "top_k": 20
}
```

Ranking: gap score DESC → transport distance DESC → approved places ASC → approval number ASC.

## 5. `compare_transport_access`

Compare nearest-public-transport statistics across urban/rural groups, states or service types.

```json
{"state": "QLD", "service_type": "Centre-Based Care", "group_by": "urban_rural"}
```

## 6. `analyse_transport_quartile_outcomes`

Compare NQS quality outcomes and authorised capacity across national transport-access quartiles.

```json
{
  "state": "QLD",
  "urban_rural": "Rural",
  "service_type": "Centre-Based Care",
  "min_group_size": 20
}
```

This tool does not infer demand or causality.


## 7. `simulate_risk_thresholds`

Compare one proposed percentile setting with the fixed P75/P25 baseline. Percentiles are always computed from the national validated Centre-Based Care sample.

```json
{
  "transport_percentile": 0.80,
  "capacity_percentile": 0.25,
  "minimum_gap_score": 3,
  "state": "QLD",
  "urban_rural": "Rural",
  "changed_service_limit": 10
}
```

## 8. `compare_risk_scenarios`

Compare two deterministic assumption sets without asking the LLM to calculate counts or differences.

```json
{
  "scenario_a": {
    "label": "Broad",
    "transport_percentile": 0.70,
    "capacity_percentile": 0.30,
    "minimum_gap_score": 3
  },
  "scenario_b": {
    "label": "Strict",
    "transport_percentile": 0.85,
    "capacity_percentile": 0.20,
    "minimum_gap_score": 3
  }
}
```

## 9. `search_policy`

Retrieve grounded passages from the locally built curated ACECQA/NQF corpus.

Input:

```json
{
  "query": "What should a regulatory authority consider before deciding how to respond?",
  "topic": "regulatory_powers",
  "top_k": 5
}
```

Output shape:

```json
{
  "query": "...",
  "topic": "regulatory_powers",
  "corpus_chunk_count": 120,
  "result_count": 5,
  "results": [
    {
      "chunk_id": "POL-regulatory_authority_powers-0004",
      "source_id": "regulatory_authority_powers",
      "source_title": "Guide to the NQF — Section 5: Regulatory Authority Powers",
      "source_url": "https://www.acecqa.gov.au/...",
      "source_kind": "guide",
      "authority_level": "official_guidance",
      "section": "...",
      "excerpt": "...",
      "retrieval_score": 8.41,
      "source_retrieved_at": "..."
    }
  ],
  "caveat": "..."
}
```

The LLM must cite returned `chunk_id` values in structured evidence. Runtime validation rejects fabricated policy chunk IDs.
