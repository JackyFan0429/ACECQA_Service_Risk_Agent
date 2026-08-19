from __future__ import annotations

import json
from pathlib import Path

from acecqa_agent.agent.tool_adapter import invoke_registered_tool
from acecqa_agent.evals.m5_harness import (
    aggregate_metrics,
    evaluate_case,
    path_get,
    validate_benchmark,
)

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = json.loads((ROOT / "evals" / "m5_benchmark.json").read_text(encoding="utf-8"))


def _set_path(target: dict, path: str, value):
    current = target
    parts = path.split(".")
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value


def _args_from_case(case: dict, tool: str) -> dict:
    args = {}
    for spec in case.get("argument_checks", []):
        if spec["tool"] != tool or "equals" not in spec:
            continue
        _set_path(args, spec["path"], spec["equals"])
    return args


def _fake_report(tool: str, args: dict, output: dict, answer: str = "ok") -> dict:
    return {
        "query": "test",
        "model": "test-model",
        "answer": {
            "answer": answer,
            "evidence": [{"source_tool": tool, "claim": "test", "policy_chunk_ids": []}],
            "methodology": [],
            "limitations": [],
        },
        "used_tools": [tool],
        "tool_trace": [
            {"sequence": 1, "event_type": "tool_call", "tool_name": tool, "call_id": "c1", "arguments": args, "output": None},
            {"sequence": 2, "event_type": "tool_output", "tool_name": tool, "call_id": "c1", "arguments": None, "output": output},
        ],
        "policy_sources": [],
        "usage": {"requests": 2, "input_tokens": 100, "output_tokens": 20, "total_tokens": 120},
        "latency_ms": 1000.0,
    }


def test_benchmark_has_expected_structure():
    assert validate_benchmark(BENCHMARK) == []
    assert len(BENCHMARK["cases"]) == 50
    assert BENCHMARK["category_counts"] == {
        "data_retrieval": 8,
        "risk_analysis": 8,
        "comparison": 6,
        "policy_rag": 8,
        "scenario_analysis": 8,
        "reliability_boundary": 12,
    }


def test_path_get_supports_list_index_and_selector():
    value = {
        "data": {
            "services": [{"name": "A"}],
            "groups": [{"group": "Rural", "count": 10}, {"group": "Urban", "count": 20}],
        }
    }
    assert path_get(value, "data.services[0].name") == "A"
    assert path_get(value, "data.groups[group=Rural].count") == 10
    assert path_get(value, "data.groups[group=Missing].count") is None


def test_output_expectations_are_consistent_with_deterministic_tools():
    """Lock M5 numerical/output expectations to the current deterministic tool layer."""
    checked = 0
    for case in BENCHMARK["cases"]:
        by_tool = {}
        for spec in case.get("output_checks", []):
            by_tool.setdefault(spec["tool"], []).append(spec)
        for tool, specs in by_tool.items():
            # Policy output is intentionally not snapshot-locked here; corpus grounding is tested separately.
            if tool == "search_policy":
                continue
            args = _args_from_case(case, tool)
            envelope = invoke_registered_tool(tool, args)
            for spec in specs:
                actual = path_get(envelope, spec["path"])
                if "equals" in spec:
                    assert actual == spec["equals"], (case["id"], spec, actual, args)
                elif "approx" in spec:
                    assert abs(float(actual) - float(spec["approx"])) <= float(spec.get("tolerance", 1e-6)), (
                        case["id"], spec, actual, args
                    )
                elif "contains" in spec:
                    assert spec["contains"].lower() in str(actual).lower(), (case["id"], spec, actual, args)
                checked += 1
    assert checked >= 60


def test_evaluator_detects_tool_and_parameter_failures():
    case = {
        "id": "X",
        "category": "data_retrieval",
        "query": "x",
        "tool_expectation": {"mode": "exact", "tools": ["search_services"]},
        "argument_checks": [{"tool": "search_services", "path": "state", "equals": "QLD"}],
    }
    output = {"ok": True, "tool": "search_services", "data": {}}
    report = _fake_report("search_services", {"state": "NSW"}, output)
    result = evaluate_case(case, report)
    assert result["status"] == "FAIL"
    assert any(item["dimension"] == "parameters" for item in result["failures"])


def test_evaluator_accepts_deterministic_output_and_evidence():
    case = {
        "id": "X",
        "category": "data_retrieval",
        "query": "x",
        "tool_expectation": {"mode": "exact", "tools": ["search_services"], "max_calls": 1},
        "argument_checks": [{"tool": "search_services", "path": "state", "equals": "QLD"}],
        "output_checks": [{"tool": "search_services", "path": "data.matched_count", "equals": 227}],
        "answer_checks": {"must_contain_all": ["227"]},
        "evidence_tools": ["search_services"],
    }
    output = {"ok": True, "tool": "search_services", "data": {"matched_count": 227}}
    report = _fake_report("search_services", {"state": "QLD"}, output, "There are 227 services.")
    result = evaluate_case(case, report)
    assert result["status"] == "PASS"


def test_policy_grounding_requires_official_resolved_source():
    case = {
        "id": "P",
        "category": "policy_rag",
        "query": "x",
        "tool_expectation": {"mode": "exact", "tools": ["search_policy"]},
        "policy_checks": {"required": True, "minimum_sources": 1, "required_domain": "acecqa.gov.au"},
        "evidence_tools": ["search_policy"],
    }
    report = _fake_report("search_policy", {"query": "x"}, {"ok": True, "tool": "search_policy", "data": {}})
    report["answer"]["evidence"][0]["policy_chunk_ids"] = ["POL-1"]
    report["policy_sources"] = [{
        "chunk_id": "POL-1", "source_title": "Guide", "source_url": "https://www.acecqa.gov.au/media/38281", "authority_level": "official_guidance"
    }]
    result = evaluate_case(case, report)
    assert result["status"] == "PASS"


def test_aggregate_metrics_and_acceptance():
    benchmark = {
        "acceptance": {
            "minimum_task_success_rate": 0.5,
            "minimum_tool_selection_accuracy": 0.5,
            "critical_cases_must_all_pass": True,
        }
    }
    result = {
        "id": "A", "category": "reliability_boundary", "critical": True, "passed": True, "status": "PASS",
        "used_tools": ["x"], "tool_call_count": 1, "dimensions": {"tool_selection": {"passed": True, "passed_checks": 1, "total_checks": 1}},
        "usage": {"requests": 2, "input_tokens": 100, "output_tokens": 20, "total_tokens": 120}, "latency_ms": 500,
    }
    metrics = aggregate_metrics(benchmark, [result])
    assert metrics["task_success_rate"] == 1.0
    assert metrics["boundary_handling_rate"] == 1.0
    assert metrics["acceptance"]["ready"] is True
