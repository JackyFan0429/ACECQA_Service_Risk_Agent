#!/usr/bin/env python3
"""Run the 50-case Milestone 5 formal benchmark against the live Agent."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path

from acecqa_agent.agent import run_copilot
from acecqa_agent.evals.m5_harness import (
    aggregate_metrics,
    evaluate_case,
    load_json,
    render_detailed_report,
    render_summary,
    validate_benchmark,
)

ROOT = Path(__file__).resolve().parent
BENCHMARK_PATH = ROOT / "evals" / "m5_benchmark.json"
RESULTS_ROOT = ROOT / "evals" / "m5_results"


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()



def _load_cases(args, benchmark):
    cases = benchmark["cases"]
    if args.case:
        cases = [case for case in cases if case["id"] == args.case]
        if not cases:
            raise SystemExit(f"Unknown case: {args.case}")
    if args.category:
        cases = [case for case in cases if case["category"] == args.category]
        if not cases:
            raise SystemExit(f"Unknown/empty category: {args.category}")
    if args.limit is not None:
        cases = cases[: args.limit]
    return cases


def _tool_call_count(report_dict):
    return sum(1 for event in report_dict.get("tool_trace", []) if event.get("event_type") == "tool_call")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Milestone 5 formal Agent benchmark.")
    parser.add_argument("--case", default=None, help="Run one benchmark case id.")
    parser.add_argument("--category", default=None, help="Run one category only.")
    parser.add_argument("--limit", type=int, default=None, help="Run only the first N selected cases (development only).")
    parser.add_argument("--list", action="store_true", help="List benchmark cases without API calls.")
    parser.add_argument("--pause", type=float, default=0.0, help="Seconds to pause between live cases.")
    parser.add_argument("--resume", type=Path, default=None, help="Resume/re-evaluate an existing run directory.")
    parser.add_argument("--retry-errors", action="store_true", help="When resuming, rerun saved cases whose raw report contains run_error.")
    parser.add_argument("--input-usd-per-1m", type=float, default=None)
    parser.add_argument("--output-usd-per-1m", type=float, default=None)
    args = parser.parse_args()

    benchmark = load_json(BENCHMARK_PATH)
    errors = validate_benchmark(benchmark)
    if errors:
        raise SystemExit("Benchmark validation failed:\n- " + "\n- ".join(errors))

    if args.list:
        for case in benchmark["cases"]:
            mark = " [CRITICAL]" if case.get("critical") else ""
            print(f"{case['id']} [{case['category']}]{mark}: {case['query']}")
        return

    cases = _load_cases(args, benchmark)
    formal_full_suite = len(cases) == benchmark["case_count"] and not args.case and not args.category and args.limit is None

    if args.resume:
        run_dir = args.resume.resolve()
        run_dir.mkdir(parents=True, exist_ok=True)
    else:
        run_dir = RESULTS_ROOT / datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir.mkdir(parents=True, exist_ok=True)

    input_price = args.input_usd_per_1m
    output_price = args.output_usd_per_1m
    if input_price is None and os.getenv("ACE_M5_INPUT_USD_PER_1M"):
        input_price = float(os.environ["ACE_M5_INPUT_USD_PER_1M"])
    if output_price is None and os.getenv("ACE_M5_OUTPUT_USD_PER_1M"):
        output_price = float(os.environ["ACE_M5_OUTPUT_USD_PER_1M"])

    results = []
    for index, case in enumerate(cases, start=1):
        print(f"\n[{index}/{len(cases)}] {case['id']} — {case['query']}")
        raw_path = run_dir / f"{case['id']}_raw.json"
        if raw_path.exists():
            existing = json.loads(raw_path.read_text(encoding="utf-8"))
            if args.retry_errors and existing.get("run_error"):
                print("  retrying previous runtime error")
                raw_path.unlink()
            else:
                print("  using existing raw result (resume mode)")
                report_dict = existing
        if not raw_path.exists():
            require_tool = bool(case.get("run", {}).get("require_tool", True))
            try:
                report = run_copilot(case["query"], require_tool=require_tool)
                report_dict = report.model_dump(mode="json")
                raw_path.write_text(json.dumps(report_dict, indent=2, ensure_ascii=False), encoding="utf-8")
            except Exception as exc:
                partial_report = getattr(exc, "report", None)
                if partial_report is not None and hasattr(partial_report, "model_dump"):
                    error_payload = partial_report.model_dump(mode="json")
                    error_payload["run_error"] = {"type": type(exc).__name__, "message": str(exc)}
                else:
                    error_payload = {
                        "query": case["query"],
                        "model": os.getenv("ACECQA_AGENT_MODEL", "unknown"),
                        "answer": {"answer": "", "evidence": [], "methodology": [], "limitations": []},
                        "used_tools": [],
                        "tool_trace": [],
                        "policy_sources": [],
                        "usage": {"requests": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                        "latency_ms": 0.0,
                    }
                    error_payload["run_error"] = {"type": type(exc).__name__, "message": str(exc)}
                raw_path.write_text(json.dumps(error_payload, indent=2, ensure_ascii=False), encoding="utf-8")
                report_dict = error_payload

        result = evaluate_case(case, report_dict)
        result["tool_call_count"] = _tool_call_count(report_dict)
        if report_dict.get("run_error"):
            result["passed"] = False
            result["status"] = "FAIL"
            result["failures"].insert(0, {
                "dimension": "runtime",
                "message": f"{report_dict['run_error']['type']}: {report_dict['run_error']['message']}",
            })
        results.append(result)
        print(f"  tools: {report_dict.get('used_tools', [])}")
        print(f"  {result['status']}")
        for failure in result["failures"]:
            print(f"  - [{failure['dimension']}] {failure['message']}")
        if args.pause and index < len(cases):
            time.sleep(args.pause)

    metrics = aggregate_metrics(
        benchmark,
        results,
        input_usd_per_1m=input_price,
        output_usd_per_1m=output_price,
    )
    if not formal_full_suite:
        metrics["acceptance"]["ready"] = False
        metrics["acceptance"]["partial_suite"] = True

    (run_dir / "case_results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = render_summary(benchmark, metrics, results)
    report = render_detailed_report(benchmark, metrics, results)
    (run_dir / "summary.md").write_text(summary, encoding="utf-8")
    (run_dir / "evaluation_report.md").write_text(report, encoding="utf-8")
    snapshot = {
        "benchmark_sha256": _sha256(BENCHMARK_PATH),
        "service_data_sha256": _sha256(ROOT / "data" / "education_services_cleaned.csv"),
        "policy_corpus_sha256": _sha256(ROOT / "data" / "policy" / "policy_chunks.jsonl"),
        "policy_manifest_sha256": _sha256(ROOT / "data" / "policy" / "corpus_manifest.json"),
    }
    (run_dir / "run_config.json").write_text(json.dumps({
        "benchmark_version": benchmark["version"],
        "formal_full_suite": formal_full_suite,
        "case_ids": [case["id"] for case in cases],
        "models_observed": sorted({row.get("model") for row in results if row.get("model")}),
        "input_usd_per_1m": input_price,
        "output_usd_per_1m": output_price,
        "snapshot": snapshot,
    }, indent=2), encoding="utf-8")

    print("\n" + summary)
    print(f"Saved summary: {run_dir / 'summary.md'}")
    print(f"Detailed report: {run_dir / 'evaluation_report.md'}")
    if not formal_full_suite:
        print("NOTE: This was a partial/development run; M5 ready is intentionally forced to NO.")


if __name__ == "__main__":
    main()
