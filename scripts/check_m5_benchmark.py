#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from acecqa_agent.evals.m5_harness import load_json, validate_benchmark

benchmark = load_json(ROOT / "evals" / "m5_benchmark.json")
errors = validate_benchmark(benchmark)
if errors:
    print("M5 benchmark integrity: FAIL")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)
print(f"M5 benchmark integrity: PASS ({len(benchmark['cases'])} cases)")
for category, count in benchmark["category_counts"].items():
    print(f"- {category}: {count}")
