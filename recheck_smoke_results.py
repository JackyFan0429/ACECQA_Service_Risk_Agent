"""Re-score an existing Milestone 2 smoke-test run without calling the API.

Usage:
    python recheck_smoke_results.py evals/results/20260819_123456

This reads the saved M2-XX_raw.json files and applies the current smoke_cases.json
and evaluator rules. It does not require OPENAI_API_KEY and does not spend tokens.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from run_smoke_tests import (
    ROOT,
    DEFAULT_CASES,
    check_answer,
    check_arguments,
    check_tools,
    find_failed_tool_outputs,
    load_suite,
)


def used_tools(report: dict[str, Any]) -> list[str]:
    value = report.get("used_tools", [])
    return list(value) if isinstance(value, list) else []


def tool_arguments_by_name(report: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for event in report.get("tool_trace", []):
        if event.get("event_type") != "tool_call" or not event.get("tool_name"):
            continue
        args = event.get("arguments") if isinstance(event.get("arguments"), dict) else {}
        result.setdefault(event["tool_name"], []).append(args)
    return result


def failed_tool_outputs(report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for event in report.get("tool_trace", []):
        if event.get("event_type") != "tool_output" or not isinstance(event.get("output"), dict):
            continue
        if event["output"].get("ok") is False:
            failures.append(event.get("tool_name") or "unknown")
    return failures


def answer_text(report: dict[str, Any]) -> str:
    answer = report.get("answer", {})
    if isinstance(answer, dict):
        return str(answer.get("answer", ""))
    return str(answer)


def main() -> None:
    parser = argparse.ArgumentParser(description="Re-score saved Milestone 2 smoke-test raw reports")
    parser.add_argument("run_dir", help="Existing evals/results/<timestamp> directory")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="Path to smoke_cases.json")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    if not run_dir.is_dir():
        raise SystemExit(f"Run directory not found: {run_dir}")

    suite = load_suite(Path(args.cases).expanduser().resolve())
    rows = []
    total_tokens = 0
    total_latency_ms = 0.0

    for case in suite["cases"]:
        raw_path = run_dir / f"{case['id']}_raw.json"
        if not raw_path.exists():
            rows.append({"id": case["id"], "critical": bool(case.get("critical")), "passed": False,
                         "tools": [], "failures": [f"Missing raw report: {raw_path.name}"]})
            continue

        report = json.loads(raw_path.read_text(encoding="utf-8"))
        tools = used_tools(report)
        args_by_tool = tool_arguments_by_name(report)
        failures: list[str] = []
        failures.extend(check_tools(tools, case.get("tool_expectation", {})))
        failures.extend(check_arguments(args_by_tool, case.get("expected_args", {})))
        failures.extend(check_answer(answer_text(report), case.get("answer_checks", {})))
        bad_outputs = failed_tool_outputs(report)
        if bad_outputs and case["id"] != "M2-10":
            failures.append(f"Tool output returned ok=false for: {bad_outputs}.")

        usage = report.get("usage", {}) if isinstance(report.get("usage"), dict) else {}
        total_tokens += int(usage.get("total_tokens", 0) or 0)
        total_latency_ms += float(report.get("latency_ms", 0.0) or 0.0)
        rows.append({"id": case["id"], "critical": bool(case.get("critical")), "passed": not failures,
                     "tools": tools, "failures": failures})

    passed = sum(r["passed"] for r in rows)
    critical_ok = all(r["passed"] for r in rows if r["critical"])
    minimum = int(suite["pass_rule"].get("minimum_passed_cases", 11))
    ready = passed >= minimum and critical_ok

    lines = [
        "# Milestone 2 Smoke Test Recheck",
        "",
        f"- Evaluator version: `{suite.get('version', 'unknown')}`",
        f"- Passed: **{passed}/{len(rows)}**",
        f"- Critical cases: **{'PASS' if critical_ok else 'FAIL'}**",
        f"- Milestone 2 ready: **{'YES' if ready else 'NO'}**",
        f"- Original run tokens: **{total_tokens}** (recheck used 0 API tokens)",
        f"- Original cumulative latency: **{total_latency_ms / 1000:.1f}s**",
        "",
        "| Case | Critical | Status | Tools |",
        "|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['id']} | {'Yes' if row['critical'] else 'No'} | {'PASS' if row['passed'] else 'FAIL'} | {', '.join(row['tools']) or 'none'} |")

    failures = [r for r in rows if not r["passed"]]
    if failures:
        lines += ["", "## Remaining failures", ""]
        for row in failures:
            lines.append(f"### {row['id']}")
            for failure in row["failures"]:
                lines.append(f"- {failure}")
            lines.append("")

    lines += [
        "", "## Acceptance rule", "",
        "Stable = at least 11/12 pass and M2-03, M2-09, M2-10, M2-12 all pass.",
        "",
        "> M2-05 intentionally remains strict: an unnecessary extra risk-score call is still counted as a routing-efficiency miss.",
    ]

    out = run_dir / "summary_rechecked.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
