#!/usr/bin/env python3
"""Re-score a completed M5 run from saved raw reports without using API tokens."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from acecqa_agent.evals.m5_harness import aggregate_metrics, evaluate_case, load_json, render_detailed_report, render_summary, validate_benchmark

ROOT = Path(__file__).resolve().parent
BENCHMARK_PATH = ROOT / "evals" / "m5_benchmark.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--input-usd-per-1m", type=float, default=None)
    parser.add_argument("--output-usd-per-1m", type=float, default=None)
    args = parser.parse_args()

    benchmark = load_json(BENCHMARK_PATH)
    errors = validate_benchmark(benchmark)
    if errors:
        raise SystemExit("Benchmark validation failed:\n- " + "\n- ".join(errors))
    run_dir = args.run_dir.resolve()
    saved_config_path = run_dir / "run_config.json"
    saved_config = json.loads(saved_config_path.read_text(encoding="utf-8")) if saved_config_path.exists() else {}
    input_price = args.input_usd_per_1m if args.input_usd_per_1m is not None else saved_config.get("input_usd_per_1m")
    output_price = args.output_usd_per_1m if args.output_usd_per_1m is not None else saved_config.get("output_usd_per_1m")
    results = []
    missing = []
    for case in benchmark["cases"]:
        raw_path = run_dir / f"{case['id']}_raw.json"
        if not raw_path.exists():
            missing.append(case["id"])
            continue
        report = json.loads(raw_path.read_text(encoding="utf-8"))
        result = evaluate_case(case, report)
        result["tool_call_count"] = sum(
            1 for event in report.get("tool_trace", []) if event.get("event_type") == "tool_call"
        )
        if report.get("run_error"):
            result["passed"] = False
            result["status"] = "FAIL"
            result["failures"].insert(0, {
                "dimension": "runtime",
                "message": f"{report['run_error']['type']}: {report['run_error']['message']}",
            })
        results.append(result)

    metrics = aggregate_metrics(
        benchmark,
        results,
        input_usd_per_1m=input_price,
        output_usd_per_1m=output_price,
    )
    if missing:
        metrics["acceptance"]["ready"] = False
        metrics["acceptance"]["missing_cases"] = missing

    (run_dir / "case_results_rechecked.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (run_dir / "metrics_rechecked.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    summary = render_summary(benchmark, metrics, results)
    report = render_detailed_report(benchmark, metrics, results)
    (run_dir / "summary_rechecked.md").write_text(summary, encoding="utf-8")
    (run_dir / "evaluation_report_rechecked.md").write_text(report, encoding="utf-8")
    print(summary)
    if missing:
        print(f"Missing raw cases: {', '.join(missing)}")
    print("Recheck used 0 API tokens.")


if __name__ == "__main__":
    main()
