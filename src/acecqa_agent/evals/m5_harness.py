from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


def normalise_text(text: str) -> str:
    """Normalise lightweight answer text before semantic marker checks.

    This is deliberately not a semantic judge. It only removes formatting and
    normalises common English contractions so equivalent answers such as
    ``can't`` and ``cannot`` are not scored differently.
    """
    text = str(text).lower()
    text = text.replace("’", "'").replace("‘", "'")
    text = re.sub(r"[*_`#>]", "", text)
    text = text.replace("–", "-").replace("—", "-")
    contractions = {
        "can't": "cannot",
        "cannot": "cannot",
        "doesn't": "does not",
        "don't": "do not",
        "isn't": "is not",
        "aren't": "are not",
        "wasn't": "was not",
        "weren't": "were not",
        "won't": "will not",
        "shouldn't": "should not",
        "wouldn't": "would not",
        "couldn't": "could not",
    }
    for source, target in contractions.items():
        text = text.replace(source, target)
    return re.sub(r"\s+", " ", text).strip()


def _coerce_selector(value: str) -> Any:
    raw = value.strip()
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    if raw.lower() == "none" or raw.lower() == "null":
        return None
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def path_get(value: Any, path: str) -> Any:
    """Tiny JSONPath-like reader.

    Supported examples:
      data.services[0].service_name
      data.groups[group=Rural].service_count
      data.quartiles[transport_access_quartile=Q4 Farthest].below_meeting_rate
    """
    current = value
    if not path:
        return current
    for part in path.split("."):
        match = re.fullmatch(r"([^\[]+)(?:\[([^\]]+)\])?", part)
        if not match:
            return None
        key, selector = match.groups()
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
        if selector is None:
            continue
        if not isinstance(current, list):
            return None
        if selector.isdigit() or (selector.startswith("-") and selector[1:].isdigit()):
            index = int(selector)
            try:
                current = current[index]
            except IndexError:
                return None
            continue
        if "=" not in selector:
            return None
        sel_key, sel_value = selector.split("=", 1)
        wanted = _coerce_selector(sel_value)
        found = None
        for item in current:
            if not isinstance(item, dict):
                continue
            actual = item.get(sel_key)
            if actual == wanted or str(actual) == str(wanted):
                found = item
                break
        if found is None:
            return None
        current = found
    return current


def _tool_events(report: dict[str, Any], event_type: str, tool_name: str) -> list[dict[str, Any]]:
    return [
        event for event in report.get("tool_trace", [])
        if event.get("event_type") == event_type and event.get("tool_name") == tool_name
    ]


def _selected_event(report: dict[str, Any], event_type: str, tool_name: str, occurrence: int = -1) -> dict[str, Any] | None:
    events = _tool_events(report, event_type, tool_name)
    if not events:
        return None
    try:
        return events[occurrence]
    except IndexError:
        return None


def _compare(actual: Any, spec: dict[str, Any]) -> bool:
    if "equals" in spec:
        expected = spec["equals"]
        if isinstance(expected, float) and isinstance(actual, (float, int)) and not isinstance(actual, bool):
            return math.isclose(float(actual), expected, rel_tol=1e-9, abs_tol=1e-9)
        return actual == expected
    if "not_equals" in spec:
        return actual != spec["not_equals"]
    if "approx" in spec:
        if not isinstance(actual, (float, int)) or isinstance(actual, bool):
            return False
        return math.isclose(
            float(actual), float(spec["approx"]), rel_tol=0.0, abs_tol=float(spec.get("tolerance", 1e-6))
        )
    if "one_of" in spec:
        return actual in spec["one_of"]
    if "contains" in spec:
        if isinstance(actual, str):
            return normalise_text(spec["contains"]) in normalise_text(actual)
        if isinstance(actual, (list, tuple, set)):
            return spec["contains"] in actual
        return False
    if "length" in spec:
        try:
            return len(actual) == int(spec["length"])
        except (TypeError, ValueError):
            return False
    if "exists" in spec:
        return (actual is not None) is bool(spec["exists"])
    for operator in ("gt", "gte", "lt", "lte"):
        if operator in spec:
            if not isinstance(actual, (int, float)) or isinstance(actual, bool):
                return False
            target = float(spec[operator])
            actual_f = float(actual)
            return {
                "gt": actual_f > target,
                "gte": actual_f >= target,
                "lt": actual_f < target,
                "lte": actual_f <= target,
            }[operator]
    return True


def _expectation_target(spec: dict[str, Any]) -> Any:
    for key in ("equals", "not_equals", "approx", "one_of", "contains", "length", "exists", "gt", "gte", "lt", "lte"):
        if key in spec:
            return {key: spec[key]}
    return None


def is_numerical_check(spec: dict[str, Any]) -> bool:
    if "approx" in spec or any(key in spec for key in ("gt", "gte", "lt", "lte")):
        return True
    value = spec.get("equals")
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_benchmark(benchmark: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    cases = benchmark.get("cases")
    if not isinstance(cases, list):
        return ["benchmark.cases must be a list"]
    expected_count = benchmark.get("case_count")
    if expected_count is not None and len(cases) != expected_count:
        errors.append(f"Expected {expected_count} cases, found {len(cases)}.")
    ids = [case.get("id") for case in cases]
    duplicates = [item for item, count in Counter(ids).items() if count > 1]
    if duplicates:
        errors.append(f"Duplicate case ids: {duplicates}")
    queries = [normalise_text(case.get("query", "")) for case in cases]
    duplicate_queries = [item for item, count in Counter(queries).items() if item and count > 1]
    if duplicate_queries:
        errors.append(f"Duplicate benchmark queries detected: {duplicate_queries[:3]}")
    expected_categories = benchmark.get("category_counts", {})
    actual_categories = Counter(case.get("category") for case in cases)
    for category, expected in expected_categories.items():
        if actual_categories.get(category, 0) != expected:
            errors.append(
                f"Category {category!r}: expected {expected}, found {actual_categories.get(category, 0)}."
            )
    for case in cases:
        if not case.get("id") or not case.get("query") or not case.get("category"):
            errors.append(f"Case missing id/query/category: {case}")
    return errors


def evaluate_case(case: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    failures: list[dict[str, str]] = []
    dimensions: dict[str, dict[str, int | bool]] = {}
    used_tools = report.get("used_tools", [])
    used_set = set(used_tools)

    def fail(dimension: str, message: str) -> None:
        failures.append({"dimension": dimension, "message": message})

    # Tool selection ---------------------------------------------------------
    tool_spec = case.get("tool_expectation")
    if tool_spec:
        mode = tool_spec.get("mode", "exact")
        expected = tool_spec.get("tools", [])
        expected_set = set(expected)
        passed = True
        if mode == "exact":
            passed = used_set == expected_set and len(used_tools) == len(expected_set)
        elif mode == "contains":
            passed = expected_set.issubset(used_set)
        elif mode == "none":
            passed = len(used_tools) == 0
        elif mode == "allowed_subset":
            passed = used_set.issubset(expected_set)
        elif mode == "any_of":
            alternatives = [set(items) for items in tool_spec.get("alternatives", [])]
            passed = any(used_set == alternative for alternative in alternatives)
        else:
            passed = False
        max_calls = tool_spec.get("max_calls")
        tool_call_count = sum(1 for event in report.get("tool_trace", []) if event.get("event_type") == "tool_call")
        if max_calls is not None and tool_call_count > int(max_calls):
            passed = False
            fail("tool_selection", f"Expected at most {max_calls} tool call(s), got {tool_call_count}.")
        if not passed and not any(item["dimension"] == "tool_selection" for item in failures):
            fail("tool_selection", f"Tool expectation {mode} {expected} not met; used {used_tools}.")
        dimensions["tool_selection"] = {"passed": passed, "passed_checks": int(passed), "total_checks": 1}

    # Arguments --------------------------------------------------------------
    arg_checks = case.get("argument_checks", [])
    arg_passed = 0
    for spec in arg_checks:
        event = _selected_event(
            report, "tool_call", spec["tool"], int(spec.get("occurrence", -1))
        )
        actual = None if event is None else path_get(event.get("arguments"), spec["path"])
        passed = event is not None and _compare(actual, spec)
        arg_passed += int(passed)
        if not passed:
            fail(
                "parameters",
                f"{spec['tool']} argument {spec['path']} expected {_expectation_target(spec)!r}, got {actual!r}.",
            )
    if arg_checks:
        dimensions["parameters"] = {
            "passed": arg_passed == len(arg_checks),
            "passed_checks": arg_passed,
            "total_checks": len(arg_checks),
        }

    # Deterministic outputs --------------------------------------------------
    output_checks = case.get("output_checks", [])
    output_passed = 0
    numerical_total = 0
    numerical_passed = 0
    for spec in output_checks:
        event = _selected_event(
            report, "tool_output", spec["tool"], int(spec.get("occurrence", -1))
        )
        actual = None if event is None else path_get(event.get("output"), spec["path"])
        passed = event is not None and _compare(actual, spec)
        output_passed += int(passed)
        if is_numerical_check(spec):
            numerical_total += 1
            numerical_passed += int(passed)
        if not passed:
            fail(
                "deterministic_output",
                f"{spec['tool']} output {spec['path']} expected {_expectation_target(spec)!r}, got {actual!r}.",
            )
    if output_checks:
        dimensions["deterministic_output"] = {
            "passed": output_passed == len(output_checks),
            "passed_checks": output_passed,
            "total_checks": len(output_checks),
        }
    if numerical_total:
        dimensions["numerical"] = {
            "passed": numerical_passed == numerical_total,
            "passed_checks": numerical_passed,
            "total_checks": numerical_total,
        }

    # Answer semantics -------------------------------------------------------
    answer_checks = case.get("answer_checks", {})
    answer_text = normalise_text(report.get("answer", {}).get("answer", ""))
    semantic_total = 0
    semantic_passed = 0
    for phrase in answer_checks.get("must_contain_all", []):
        semantic_total += 1
        passed = normalise_text(phrase) in answer_text
        semantic_passed += int(passed)
        if not passed:
            fail("answer_semantics", f"Answer missing required marker: {phrase!r}.")
    for group in answer_checks.get("must_contain_any_groups", []):
        semantic_total += 1
        passed = any(normalise_text(item) in answer_text for item in group)
        semantic_passed += int(passed)
        if not passed:
            fail("answer_semantics", f"Answer missing all alternatives in group: {group!r}.")
    for phrase in answer_checks.get("forbidden_any", []):
        semantic_total += 1
        passed = normalise_text(phrase) not in answer_text
        semantic_passed += int(passed)
        if not passed:
            fail("answer_semantics", f"Answer contained forbidden claim: {phrase!r}.")
    if semantic_total:
        dimensions["answer_semantics"] = {
            "passed": semantic_passed == semantic_total,
            "passed_checks": semantic_passed,
            "total_checks": semantic_total,
        }

    # Evidence grounding -----------------------------------------------------
    evidence_tools = case.get("evidence_tools", [])
    if evidence_tools:
        evidence = report.get("answer", {}).get("evidence", [])
        evidence_sources = {item.get("source_tool") for item in evidence if isinstance(item, dict)}
        missing = [tool for tool in evidence_tools if tool not in evidence_sources]
        passed = not missing
        if missing:
            fail("evidence_grounding", f"Final answer evidence missing source tool(s): {missing}.")
        dimensions["evidence_grounding"] = {
            "passed": passed,
            "passed_checks": len(evidence_tools) - len(missing),
            "total_checks": len(evidence_tools),
        }

    # Policy grounding -------------------------------------------------------
    policy_checks = case.get("policy_checks")
    if policy_checks and policy_checks.get("required"):
        sources = report.get("policy_sources", [])
        minimum = int(policy_checks.get("minimum_sources", 1))
        passed_checks = 0
        total_checks = 1
        count_ok = len(sources) >= minimum
        passed_checks += int(count_ok)
        if not count_ok:
            fail("policy_grounding", f"Expected at least {minimum} resolved policy source(s), got {len(sources)}.")
        required_domain = policy_checks.get("required_domain")
        if required_domain:
            total_checks += 1
            domain_ok = bool(sources) and all(
                (urlparse(str(source.get("source_url", ""))).hostname or "").endswith(required_domain)
                for source in sources
            )
            passed_checks += int(domain_ok)
            if not domain_ok:
                fail("policy_grounding", f"Policy source URLs were not all from {required_domain}.")
        allowed_authority = policy_checks.get("allowed_authority_levels")
        if allowed_authority:
            total_checks += 1
            authority_ok = bool(sources) and all(
                source.get("authority_level") in allowed_authority for source in sources
            )
            passed_checks += int(authority_ok)
            if not authority_ok:
                fail("policy_grounding", "Resolved policy source authority level was outside the allowed set.")
        dimensions["policy_grounding"] = {
            "passed": passed_checks == total_checks,
            "passed_checks": passed_checks,
            "total_checks": total_checks,
        }

    passed = not failures
    return {
        "id": case["id"],
        "category": case["category"],
        "critical": bool(case.get("critical", False)),
        "query": case["query"],
        "passed": passed,
        "status": "PASS" if passed else "FAIL",
        "used_tools": used_tools,
        "dimensions": dimensions,
        "failures": failures,
        "usage": report.get("usage", {}),
        "latency_ms": float(report.get("latency_ms", 0.0)),
        "model": report.get("model"),
    }


def _dimension_accuracy(results: Iterable[dict[str, Any]], dimension: str) -> tuple[int, int, float | None]:
    passed = total = 0
    for result in results:
        spec = result.get("dimensions", {}).get(dimension)
        if not spec:
            continue
        passed += int(spec.get("passed_checks", 0))
        total += int(spec.get("total_checks", 0))
    return passed, total, (passed / total if total else None)


def aggregate_metrics(
    benchmark: dict[str, Any],
    results: list[dict[str, Any]],
    *,
    input_usd_per_1m: float | None = None,
    output_usd_per_1m: float | None = None,
) -> dict[str, Any]:
    total_cases = len(results)
    passed_cases = sum(result["passed"] for result in results)
    category_rows: dict[str, dict[str, Any]] = {}
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        by_category[result["category"]].append(result)
    for category, rows in by_category.items():
        passed = sum(row["passed"] for row in rows)
        category_rows[category] = {
            "passed": passed,
            "total": len(rows),
            "rate": passed / len(rows) if rows else None,
        }

    dimensions = {}
    for name in (
        "tool_selection",
        "parameters",
        "deterministic_output",
        "numerical",
        "answer_semantics",
        "evidence_grounding",
        "policy_grounding",
    ):
        passed, total, rate = _dimension_accuracy(results, name)
        dimensions[name] = {"passed_checks": passed, "total_checks": total, "accuracy": rate}

    boundary_rows = [row for row in results if row["category"] == "reliability_boundary"]
    boundary_passed = sum(row["passed"] for row in boundary_rows)
    critical_rows = [row for row in results if row["critical"]]
    critical_pass = all(row["passed"] for row in critical_rows) if critical_rows else True

    total_input = sum(int(row.get("usage", {}).get("input_tokens", 0)) for row in results)
    total_output = sum(int(row.get("usage", {}).get("output_tokens", 0)) for row in results)
    total_tokens = sum(int(row.get("usage", {}).get("total_tokens", 0)) for row in results)
    total_requests = sum(int(row.get("usage", {}).get("requests", 0)) for row in results)
    total_latency_ms = sum(float(row.get("latency_ms", 0.0)) for row in results)
    total_tool_calls = 0
    for row in results:
        # used_tools is unique tools; actual tool calls are not stored in result. The runner fills this later if present.
        total_tool_calls += int(row.get("tool_call_count", len(row.get("used_tools", []))))

    cost = None
    if input_usd_per_1m is not None and output_usd_per_1m is not None:
        cost = total_input / 1_000_000 * input_usd_per_1m + total_output / 1_000_000 * output_usd_per_1m

    metrics = {
        "case_count": total_cases,
        "passed_cases": passed_cases,
        "task_success_rate": passed_cases / total_cases if total_cases else None,
        "critical_case_count": len(critical_rows),
        "critical_cases_pass": critical_pass,
        "boundary_passed": boundary_passed,
        "boundary_total": len(boundary_rows),
        "boundary_handling_rate": boundary_passed / len(boundary_rows) if boundary_rows else None,
        "category_results": category_rows,
        "dimensions": dimensions,
        "usage": {
            "total_requests": total_requests,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_tokens,
            "avg_tokens_per_query": total_tokens / total_cases if total_cases else None,
            "total_latency_ms": total_latency_ms,
            "avg_latency_ms": total_latency_ms / total_cases if total_cases else None,
            "total_tool_calls": total_tool_calls,
            "avg_tool_calls_per_query": total_tool_calls / total_cases if total_cases else None,
        },
        "estimated_cost_usd": cost,
        "estimated_cost_per_query_usd": cost / total_cases if cost is not None and total_cases else None,
        "pricing": {
            "input_usd_per_1m": input_usd_per_1m,
            "output_usd_per_1m": output_usd_per_1m,
            "note": "Pricing is user-supplied; the benchmark does not hard-code model prices.",
        },
    }
    metrics["acceptance"] = evaluate_acceptance(benchmark, metrics, results)
    return metrics


def evaluate_acceptance(
    benchmark: dict[str, Any], metrics: dict[str, Any], results: list[dict[str, Any]]
) -> dict[str, Any]:
    rule = benchmark.get("acceptance", {})
    checks: list[dict[str, Any]] = []

    def add(name: str, actual: float | bool | None, operator: str, target: Any, passed: bool) -> None:
        checks.append({"name": name, "actual": actual, "operator": operator, "target": target, "passed": passed})

    thresholds = [
        ("task_success_rate", metrics.get("task_success_rate")),
        ("tool_selection_accuracy", metrics["dimensions"]["tool_selection"]["accuracy"]),
        ("parameter_accuracy", metrics["dimensions"]["parameters"]["accuracy"]),
        ("deterministic_output_accuracy", metrics["dimensions"]["deterministic_output"]["accuracy"]),
        ("numerical_accuracy", metrics["dimensions"]["numerical"]["accuracy"]),
        ("policy_grounding_rate", metrics["dimensions"]["policy_grounding"]["accuracy"]),
        ("boundary_handling_rate", metrics.get("boundary_handling_rate")),
    ]
    for key, actual in thresholds:
        target = rule.get(f"minimum_{key}")
        if target is None:
            continue
        passed = actual is not None and actual >= float(target)
        add(key, actual, ">=", float(target), passed)

    if rule.get("critical_cases_must_all_pass", True):
        passed = bool(metrics.get("critical_cases_pass"))
        add("critical_cases", passed, "==", True, passed)

    ready = bool(checks) and all(check["passed"] for check in checks)
    return {"ready": ready, "checks": checks}


def render_summary(benchmark: dict[str, Any], metrics: dict[str, Any], results: list[dict[str, Any]]) -> str:
    def pct(value: float | None) -> str:
        return "n/a" if value is None else f"{value * 100:.1f}%"

    lines = [
        "# Milestone 5 Formal Evaluation Summary",
        "",
        f"- Benchmark: **{benchmark.get('suite', 'M5')} v{benchmark.get('version', '')}**",
        f"- Cases: **{metrics['case_count']}**",
        f"- Passed: **{metrics['passed_cases']}/{metrics['case_count']}**",
        f"- Task Success Rate: **{pct(metrics['task_success_rate'])}**",
        f"- Critical cases: **{'PASS' if metrics['critical_cases_pass'] else 'FAIL'}**",
        f"- Milestone 5 ready: **{'YES' if metrics['acceptance']['ready'] else 'NO'}**",
        "",
        "## Core metrics",
        "",
        "| Metric | Result |",
        "|---|---:|",
        f"| Tool Selection Accuracy | {pct(metrics['dimensions']['tool_selection']['accuracy'])} |",
        f"| Tool Parameter Accuracy | {pct(metrics['dimensions']['parameters']['accuracy'])} |",
        f"| Deterministic Output Accuracy | {pct(metrics['dimensions']['deterministic_output']['accuracy'])} |",
        f"| Numerical Accuracy | {pct(metrics['dimensions']['numerical']['accuracy'])} |",
        f"| Evidence Grounding Accuracy | {pct(metrics['dimensions']['evidence_grounding']['accuracy'])} |",
        f"| Policy Grounding Rate | {pct(metrics['dimensions']['policy_grounding']['accuracy'])} |",
        f"| Boundary Handling Rate | {pct(metrics['boundary_handling_rate'])} |",
        f"| Avg Tokens / Query | {metrics['usage']['avg_tokens_per_query']:.0f} |",
        f"| Avg Latency | {metrics['usage']['avg_latency_ms'] / 1000:.2f}s |",
        f"| Avg Tool Calls / Query | {metrics['usage']['avg_tool_calls_per_query']:.2f} |",
    ]
    if metrics.get("estimated_cost_per_query_usd") is not None:
        lines.append(f"| Estimated Cost / Query | ${metrics['estimated_cost_per_query_usd']:.5f} |")

    lines.extend(["", "## Category results", "", "| Category | Passed | Rate |", "|---|---:|---:|"])
    for category in benchmark.get("category_counts", {}):
        row = metrics["category_results"].get(category, {"passed": 0, "total": 0, "rate": None})
        lines.append(f"| {category} | {row['passed']}/{row['total']} | {pct(row['rate'])} |")

    lines.extend(["", "## Acceptance checks", "", "| Check | Actual | Target | Status |", "|---|---:|---:|---|"])
    for check in metrics["acceptance"]["checks"]:
        actual = check["actual"]
        if isinstance(actual, float):
            actual_display = pct(actual)
        else:
            actual_display = str(actual)
        target = check["target"]
        target_display = pct(target) if isinstance(target, float) else str(target)
        lines.append(
            f"| {check['name']} | {actual_display} | {check['operator']} {target_display} | {'PASS' if check['passed'] else 'FAIL'} |"
        )

    failed = [row for row in results if not row["passed"]]
    if failed:
        lines.extend(["", "## Failed cases"])
        for row in failed:
            lines.extend(["", f"### {row['id']} — {row['category']}"])
            lines.append(f"Query: {row['query']}")
            for failure in row["failures"]:
                lines.append(f"- **{failure['dimension']}**: {failure['message']}")
    return "\n".join(lines) + "\n"


def render_detailed_report(benchmark: dict[str, Any], metrics: dict[str, Any], results: list[dict[str, Any]]) -> str:
    summary = render_summary(benchmark, metrics, results)
    lines = [summary, "# Case-by-case results", "", "| Case | Category | Critical | Status | Tools | Tokens | Latency |", "|---|---|---:|---|---|---:|---:|"]
    for row in results:
        lines.append(
            f"| {row['id']} | {row['category']} | {'Yes' if row['critical'] else 'No'} | {row['status']} | "
            f"{', '.join(row['used_tools']) or 'none'} | {row.get('usage', {}).get('total_tokens', 0)} | {row.get('latency_ms', 0.0) / 1000:.2f}s |"
        )
    lines.extend([
        "",
        "## Evaluation design notes",
        "",
        "- v1.0 uses deterministic trace/output checks as the primary evaluator; it does not use an LLM-as-judge.",
        "- Answer text checks are intentionally lightweight and are used mainly for reliability/boundary semantics.",
        "- Policy grounding is validated from resolved policy chunk citations, not from model-written URLs.",
        "- Cost is reported only when token prices are explicitly supplied at evaluation time.",
        "- A benchmark PASS demonstrates performance on this fixed test set; it is not proof of regulatory validity or policy optimality.",
    ])
    return "\n".join(lines) + "\n"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
