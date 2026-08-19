import json

from acecqa_agent.agent.tool_adapter import TOOL_SPECS, invoke_registered_tool, invoke_registered_tool_json


def test_six_agent_tools_are_registered():
    assert list(TOOL_SPECS) == [
        "search_services",
        "get_service_profile",
        "calculate_risk_score",
        "find_high_risk_services",
        "compare_transport_access",
        "analyse_transport_quartile_outcomes",
    ]


def test_agent_adapter_runs_qld_rural_priority_tool():
    result = invoke_registered_tool(
        "find_high_risk_services",
        {
            "state": "QLD",
            "urban_rural": "Rural",
            "service_type": "Centre-Based Care",
            "top_k": 20,
            "minimum_gap_score": 3,
        },
    )
    assert result["ok"] is True
    assert result["data"]["matched_count"] == 21
    assert result["data"]["services"][0]["service_approval_number"] == "SE-40000427"


def test_agent_adapter_returns_model_visible_scope_error():
    result = invoke_registered_tool(
        "find_high_risk_services",
        {
            "state": "QLD",
            "urban_rural": "Rural",
            "service_type": "Family Day Care",
            "top_k": 10,
            "minimum_gap_score": 2,
        },
    )
    assert result["ok"] is False
    assert "Centre-Based Care" in result["message"]


def test_agent_adapter_rejects_invalid_state():
    result = invoke_registered_tool("search_services", {"state": "Queensland", "limit": 5})
    assert result["ok"] is False
    assert result["error_type"] == "ValidationError"


def test_agent_adapter_json_is_machine_readable():
    payload = invoke_registered_tool_json(
        "calculate_risk_score", {"service_approval_number": "SE-40000427"}
    )
    parsed = json.loads(payload)
    assert parsed["ok"] is True
    assert parsed["data"]["gap_score"] == 3
