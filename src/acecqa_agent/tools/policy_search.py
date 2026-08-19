"""Policy retrieval tool for curated ACECQA/NQF guidance."""

from __future__ import annotations

from acecqa_agent.rag import get_policy_repository
from acecqa_agent.schemas import PolicySearchInput, PolicySearchOutput, PolicySearchResult


def search_policy(inputs: PolicySearchInput) -> PolicySearchOutput:
    repo = get_policy_repository()
    matches = repo.search(inputs.query, top_k=inputs.top_k, topic=inputs.topic)
    results = [
        PolicySearchResult(
            chunk_id=item["chunk_id"],
            source_id=item["source_id"],
            source_title=item["source_title"],
            source_url=item["source_url"],
            source_kind=item.get("source_kind", "official_webpage"),
            authority_level=item.get("authority_level", "official_guidance"),
            section=item.get("section"),
            excerpt=item.get("text", ""),
            retrieval_score=item["retrieval_score"],
            source_retrieved_at=item.get("source_retrieved_at"),
        )
        for item in matches
    ]
    return PolicySearchOutput(
        query=inputs.query,
        topic=inputs.topic,
        corpus_chunk_count=repo.chunk_count,
        result_count=len(results),
        results=results,
        caveat=(
            "Retrieved material is official ACECQA guidance/reference material. The Guide to the NQF "
            "is not legal advice; the National Law and Regulations take precedence."
        ),
    )
