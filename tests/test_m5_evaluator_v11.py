import json
from pathlib import Path

from acecqa_agent.evals.m5_harness import evaluate_case, normalise_text

ROOT = Path(__file__).resolve().parents[1]


def _case(case_id: str):
    benchmark = json.loads((ROOT / "evals" / "m5_benchmark.json").read_text())
    return next(case for case in benchmark["cases"] if case["id"] == case_id)


def test_normalise_text_handles_curly_contractions():
    assert "cannot identify" in normalise_text("I can’t identify services")
    assert "does not include" in normalise_text("It doesn’t include waitlists")


def test_b02_equivalent_refusal_language_passes():
    report = {
        "answer": {"answer": "I can’t identify services with the longest waiting lists: this dataset has capacity but not waitlist counts.", "evidence": []},
        "used_tools": [],
        "tool_trace": [],
        "policy_sources": [],
        "usage": {},
        "latency_ms": 0,
    }
    result = evaluate_case(_case("M5-B02"), report)
    assert result["passed"]


def test_b10_no_profile_found_language_passes():
    report = {
        "answer": {"answer": "No profile was found for service approval number SE-99999999.", "evidence": []},
        "used_tools": ["get_service_profile"],
        "tool_trace": [
            {"event_type": "tool_call", "tool_name": "get_service_profile", "arguments": {"service_approval_number": "SE-99999999"}},
            {"event_type": "tool_output", "tool_name": "get_service_profile", "output": {"ok": False, "error_type": "ValueError", "message": "Unknown service_approval_number: SE-99999999"}},
        ],
        "policy_sources": [],
        "usage": {},
        "latency_ms": 0,
    }
    result = evaluate_case(_case("M5-B10"), report)
    assert result["passed"]


def test_p07_allows_one_refinement_retry_with_same_policy_tool():
    report = {
        "answer": {
            "answer": "Assessment and rating compares services with the NQS and supports continuous improvement.",
            "evidence": [{"source_tool": "search_policy", "claim": "purpose", "policy_chunk_ids": ["POL-x"]}],
        },
        "used_tools": ["search_policy"],
        "tool_trace": [
            {"event_type": "tool_call", "tool_name": "search_policy", "arguments": {}},
            {"event_type": "tool_output", "tool_name": "search_policy", "output": {}},
            {"event_type": "tool_call", "tool_name": "search_policy", "arguments": {}},
            {"event_type": "tool_output", "tool_name": "search_policy", "output": {}},
        ],
        "policy_sources": [{"source_url": "https://www.acecqa.gov.au/example", "authority_level": "official_guidance"}],
        "usage": {},
        "latency_ms": 0,
    }
    result = evaluate_case(_case("M5-P07"), report)
    assert result["passed"]
