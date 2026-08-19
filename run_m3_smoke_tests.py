#!/usr/bin/env python3
"""Milestone 3 live smoke test: policy RAG routing + data/policy composition."""
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path

from acecqa_agent.agent import run_copilot

ROOT = Path(__file__).resolve().parent
CASES_PATH = ROOT / "evals" / "m3_cases.json"
CORPUS_PATH = ROOT / "data" / "policy" / "policy_chunks.jsonl"


def normalise(text: str) -> str:
    text = re.sub(r"[*_`#>]", "", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def evaluate(case: dict, report) -> list[str]:
    failures: list[str] = []
    used = set(report.used_tools)
    for tool in case.get("required_tools", []):
        if tool not in used:
            failures.append(f"Required tool not used: {tool}")
    for tool in case.get("forbidden_tools", []):
        if tool in used:
            failures.append(f"Forbidden tool used: {tool}")

    answer = normalise(report.answer.answer)
    alternatives = [normalise(x) for x in case.get("answer_any", [])]
    if alternatives and not any(x in answer for x in alternatives):
        failures.append(f"Answer missed required semantic markers: {case['answer_any']}")
    for phrase in case.get("forbidden_any", []):
        if normalise(phrase) in answer:
            failures.append(f"Answer contained forbidden claim: {phrase}")

    if case.get("require_policy_sources"):
        if not report.policy_sources:
            failures.append("No grounded policy source was resolved from retrieved chunk ids.")
        for source in report.policy_sources:
            if "acecqa.gov.au" not in source.source_url:
                failures.append(f"Non-ACECQA policy source surfaced: {source.source_url}")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", default=None)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--pause", type=float, default=0.0)
    args = parser.parse_args()

    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    if args.list:
        for case in cases:
            mark = " [CRITICAL]" if case.get("critical") else ""
            print(f"{case['id']}{mark}: {case['query']}")
        return

    if not CORPUS_PATH.exists():
        raise SystemExit("Policy corpus missing. First run: python scripts/ingest_policy.py")

    if args.case:
        cases = [case for case in cases if case["id"] == args.case]
        if not cases:
            raise SystemExit(f"Unknown case: {args.case}")

    run_dir = ROOT / "evals" / "m3_results" / datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    total_tokens = 0
    total_latency = 0.0

    for case in cases:
        print(f"\n[{case['id']}] {case['query']}")
        try:
            report = run_copilot(case["query"])
            raw_path = run_dir / f"{case['id']}_raw.json"
            raw_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
            failures = evaluate(case, report)
            total_tokens += report.usage.total_tokens
            total_latency += report.latency_ms
            status = "PASS" if not failures else "FAIL"
            print(f"  tools: {report.used_tools}")
            print(f"  policy sources: {len(report.policy_sources)}")
            print(f"  {status}")
            for failure in failures:
                print(f"  - {failure}")
            rows.append({"id": case["id"], "critical": case.get("critical", False), "status": status, "tools": report.used_tools, "failures": failures})
        except Exception as exc:
            print(f"  ERROR: {type(exc).__name__}: {exc}")
            rows.append({"id": case["id"], "critical": case.get("critical", False), "status": "FAIL", "tools": [], "failures": [f"{type(exc).__name__}: {exc}"]})
        if args.pause:
            time.sleep(args.pause)

    passed = sum(row["status"] == "PASS" for row in rows)
    critical_pass = all(row["status"] == "PASS" for row in rows if row["critical"])
    full_suite = len(cases) == 8
    ready = full_suite and passed >= 7 and critical_pass

    lines = [
        "# Milestone 3 Smoke Test Summary",
        "",
        f"- Passed: **{passed}/{len(rows)}**",
        f"- Critical cases: **{'PASS' if critical_pass else 'FAIL'}**",
        f"- Milestone 3 ready: **{'YES' if ready else 'NO'}**" if full_suite else "- Partial suite: **YES**",
        f"- Total tokens: **{total_tokens}**",
        f"- Cumulative API latency: **{total_latency / 1000:.1f}s**",
        "",
        "| Case | Critical | Status | Tools |",
        "|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['id']} | {'Yes' if row['critical'] else 'No'} | {row['status']} | {', '.join(row['tools']) or 'none'} |")
    failures = [row for row in rows if row["status"] == "FAIL"]
    if failures:
        lines.extend(["", "## Failures"])
        for row in failures:
            lines.extend(["", f"### {row['id']}"])
            for failure in row["failures"]:
                lines.append(f"- {failure}")
    lines.extend([
        "",
        "## Acceptance rule",
        "",
        "Stable = at least 7/8 pass and all critical cases M3-02, M3-04, M3-05, M3-07, M3-08 pass.",
    ])
    summary = "\n".join(lines) + "\n"
    (run_dir / "summary.md").write_text(summary, encoding="utf-8")
    (run_dir / "summary.json").write_text(json.dumps({"rows": rows, "passed": passed, "critical_pass": critical_pass, "ready": ready, "total_tokens": total_tokens, "latency_ms": total_latency}, indent=2), encoding="utf-8")
    print("\n" + summary)
    print(f"Saved: {run_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
