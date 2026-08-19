"""Direct demo of the deterministic policy retrieval layer (no LLM/API call)."""
from __future__ import annotations

import argparse

from acecqa_agent.schemas import PolicySearchInput
from acecqa_agent.tools import search_policy


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--topic", default=None)
    args = parser.parse_args()
    result = search_policy(PolicySearchInput(query=args.query, top_k=args.top_k, topic=args.topic))
    print(f"Results: {result.result_count}/{result.corpus_chunk_count} chunks\n")
    for index, item in enumerate(result.results, start=1):
        print(f"[{index}] {item.chunk_id} score={item.retrieval_score:.3f}")
        print(item.source_title)
        if item.section:
            print(f"Section: {item.section}")
        print(item.source_url)
        print(item.excerpt[:700].replace("\n", " "))
        print()


if __name__ == "__main__":
    main()
