#!/usr/bin/env python3
"""Milestone 4 live smoke test: deterministic scenario routing and interpretation."""
from __future__ import annotations

import argparse
import json
import math
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from acecqa_agent.agent import run_copilot

ROOT = Path(__file__).resolve().parent
CASES_PATH = ROOT / "evals" / "m4_cases.json"


def normalise(text: str) -> str:
    text = re.sub(r"[*_`#>]", "", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def dotted_get(value: Any, path: str) -> Any:
    current = value
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def tool_events(report, event_type: str, tool_name: str):
    return [
        event for event in report.tool_trace
        if event.event_type == event_type and event.tool_name == tool_name
    ]


def check_expectation(actual: Any, spec: dict) -> bool:
    if "equals" in spec:
        expected = spec["equals"]
        if isinstance(expected, float) and isinstance(actual, (float, int)):
            return math.isclose(float(actual), expected, rel_tol=1e-9, abs_tol=1e-9)
        return actual == expected
    if "approx" in spec:
        if not isinstance(actual, (float, int)):
            return False
        tolerance = float(spec.get("tolerance", 1e-6))
        return math.isclose(float(actual), float(spec["approx"]), rel_tol=0.0, abs_tol=tolerance)
    return True


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
        failures.append(f"Answer missed semantic markers: {case['answer_any']}")
    for phrase in case.get("forbidden_any", []):
        if normalise(phrase) in answer:
            failures.append(f"Answer contained forbidden claim: {phrase}")

    for spec in case.get("expected_arguments", []):
        events = tool_events(report, "tool_call", spec["tool"])
        if not events:
            failures.append(f"No tool call available for argument check: {spec['tool']}")
            continue
        actual = dotted_get(events[-1].arguments, spec["path"])
        if not check_expectation(actual, spec):
            target = spec.get("equals", spec.get("approx"))
            failures.append(
                f"{spec['tool']} argument {spec['path']} expected {target!r}, got {actual!r}."
            )

    for spec in case.get("expected_outputs", []):
        events = tool_events(report, "tool_output", spec["tool"])
        if not events:
            failures.append(f"No tool output available for deterministic check: {spec['tool']}")
            continue
        actual = dotted_get(events[-1].output, spec["path"])
        if not check_expectation(actual, spec):
            target = spec.get("equals", spec.get("approx"))
            failures.append(
                f"{spec['tool']} output {spec['path']} expected {target!r}, got {actual!r}."
            )
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

    if args.case:
        cases = [case for case in cases if case["id"] == args.case]
        if not cases:
            raise SystemExit(f"Unknown case: {args.case}")

    run_dir = ROOT / "evals" / "m4_results" / datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    total_tokens = 0
    total_latency = 0.0

    for case in cases:
        print(f"\n[{case['id']}] {case['query']}")
        try:
            report = run_copilot(case["query"])
            (run_dir / f"{case['id']}_raw.json").write_text(
                report.model_dump_json(indent=2), encoding="utf-8"
            )
            failures = evaluate(case, report)
            total_tokens += report.usage.total_tokens
            total_latency += report.latency_ms
            status = "PASS" if not failures else "FAIL"
            print(f"  tools: {report.used_tools}")
            print(f"  {status}")
            for failure in failures:
                print(f"  - {failure}")
            rows.append({
                "id": case["id"],
                "critical": case.get("critical", False),
                "status": status,
                "tools": report.used_tools,
                "failures": failures,
            })
        except Exception as exc:
            print(f"  ERROR: {type(exc).__name__}: {exc}")
            rows.append({
                "id": case["id"],
                "critical": case.get("critical", False),
                "status": "FAIL",
                "tools": [],
                "failures": [f"{type(exc).__name__}: {exc}"],
            })
        if args.pause:
            time.sleep(args.pause)

    passed = sum(row["status"] == "PASS" for row in rows)
    critical_pass = all(row["status"] == "PASS" for row in rows if row["critical"])
    full_suite = len(cases) == 8
    ready = full_suite and passed >= 7 and critical_pass

    lines = [
        "# Milestone 4 Smoke Test Summary",
        "",
        f"- Passed: **{passed}/{len(rows)}**",
        f"- Critical cases: **{'PASS' if critical_pass else 'FAIL'}**",
        f"- Milestone 4 ready: **{'YES' if ready else 'NO'}**" if full_suite else "- Partial suite: **YES**",
        f"- Total tokens: **{total_tokens}**",
        f"- Cumulative API latency: **{total_latency / 1000:.1f}s**",
        "",
        "| Case | Critical | Status | Tools |",
        "|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['id']} | {'Yes' if row['critical'] else 'No'} | {row['status']} | "
            f"{', '.join(row['tools']) or 'none'} |"
        )
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
        "Stable = at least 7/8 pass and all critical cases M4-02, M4-04, M4-06, M4-07, M4-08 pass.",
    ])
    summary = "\n".join(lines) + "\n"
    (run_dir / "summary.md").write_text(summary, encoding="utf-8")
    (run_dir / "summary.json").write_text(
        json.dumps({
            "rows": rows,
            "passed": passed,
            "critical_pass": critical_pass,
            "ready": ready,
            "total_tokens": total_tokens,
            "latency_ms": total_latency,
        }, indent=2),
        encoding="utf-8",
    )
    print("\n" + summary)
    print(f"Saved: {run_dir / 'summary.md'}")


if __name__ == "__main__":
    main()
