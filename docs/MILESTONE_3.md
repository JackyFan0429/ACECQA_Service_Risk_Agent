# Milestone 3 — Policy-grounded Single Agent

## Goal

Upgrade the v0.2 data Agent into a business decision-support Agent by adding policy retrieval as a seventh tool.

The target behaviour is:

```text
User question
    ↓
Agent decides what evidence is needed
    ├── analytics tool(s) → service/data evidence
    └── search_policy()   → ACECQA/NQF evidence
    ↓
Grounding validator
    ↓
Decision-oriented answer + traceable policy sources + limitations
```

## Definition of Done

Milestone 3 is complete when all of the following are true:

1. Curated official ACECQA source manifest exists.
2. Reproducible ingestion script downloads, cleans and chunks the sources.
3. `search_policy()` returns stable chunk IDs and source metadata.
4. The seventh tool is exposed through the same Pydantic/FunctionTool adapter as analytics tools.
5. Policy claims must cite policy chunk IDs actually returned in the run.
6. Application code resolves the final source titles/URLs from the tool trace.
7. The Agent distinguishes ACECQA from state/territory regulatory authorities.
8. The Agent never treats risk score as proof of non-compliance or an automatic enforcement trigger.
9. Data + policy questions call both evidence layers.
10. Offline tests pass, then the live eight-case smoke test reaches at least 7/8 with every critical case passing.

## Why BM25 first

The first retrieval implementation is deliberately small and deterministic:

- no vector database
- no embedding API cost
- no second LLM in the retrieval path
- inspectable ranking
- simple local deployment

This is appropriate for a small curated policy corpus. If formal retrieval evaluation later shows weak recall for semantic paraphrases, add an embedding reranker as an evidence-driven iteration rather than an architectural prerequisite.

## Guardrail: data evidence is not policy evidence

A service can rank highly because it has overlapping transport, NQS and authorised-capacity gaps. That ranking answers **which services deserve analyst attention first**. It does not answer **which legal/compliance action is justified**.

Policy retrieval can provide regulatory principles and available tools, but a recommendation must preserve uncertainty and context. Formal regulatory action may depend on facts not present in the QBUS dataset, including the nature of an issue, risk to children, compliance history and other case-specific evidence.

## Acceptance query

```text
Find the 5 highest-risk rural Centre-Based Care services in Queensland
and explain what the relevant regulatory authority should consider
before deciding how to respond.
```

Expected high-level trace:

```text
find_high_risk_services(
  state="QLD",
  urban_rural="Rural",
  service_type="Centre-Based Care",
  top_k=5,
  minimum_gap_score=3
)

search_policy(
  query="regulatory response proportionality risk to children compliance history ...",
  top_k=...
)
```

The final answer should preserve the deterministic ranking, explain that it is a prioritisation screen, and ground regulatory-response considerations in retrieved official sources.
