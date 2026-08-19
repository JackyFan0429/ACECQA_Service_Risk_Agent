"""CLI demo for milestone 4: analytics + scenario analysis + policy retrieval -> grounded answer."""

from __future__ import annotations

import argparse
import json

from acecqa_agent.agent import run_copilot

DEFAULT_QUERY = "Find the highest-risk rural Centre-Based Care services in Queensland."


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ACECQA Service Risk Copilot")
    parser.add_argument("query", nargs="?", default=DEFAULT_QUERY)
    parser.add_argument("--model", default=None, help="Override ACECQA_AGENT_MODEL")
    parser.add_argument("--show-trace", action="store_true", help="Print tool-call audit trace")
    parser.add_argument("--json", action="store_true", help="Print the complete run report as JSON")
    args = parser.parse_args()

    try:
        report = run_copilot(args.query, model=args.model)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    if args.json:
        print(report.model_dump_json(indent=2))
        return

    print(report.answer.answer)

    if report.answer.evidence:
        print("\nEvidence")
        for item in report.answer.evidence:
            refs = f" ({', '.join(item.policy_chunk_ids)})" if item.policy_chunk_ids else ""
            print(f"- [{item.source_tool}] {item.claim}{refs}")

    if report.policy_sources:
        print("\nPolicy sources")
        for source in report.policy_sources:
            section = f" — {source.section}" if source.section else ""
            print(f"- [{source.chunk_id}] {source.source_title}{section}")
            print(f"  {source.source_url}")

    if report.answer.methodology:
        print("\nMethodology")
        for item in report.answer.methodology:
            print(f"- {item}")

    if report.answer.limitations:
        print("\nLimitations")
        for item in report.answer.limitations:
            print(f"- {item}")

    print(f"\nTools used: {', '.join(report.used_tools)}")
    print(
        f"Usage: {report.usage.requests} model request(s), "
        f"{report.usage.total_tokens} tokens; latency {report.latency_ms:.0f} ms"
    )

    if args.show_trace:
        print("\nTool trace")
        print(json.dumps([item.model_dump(mode="json") for item in report.tool_trace], indent=2))


if __name__ == "__main__":
    main()
