from __future__ import annotations

from fastapi.testclient import TestClient

from acecqa_agent.agent.runtime import (
    AgentRunReport,
    AgentUsageSummary,
    GroundedAgentAnswer,
    GroundedEvidence,
    ToolTraceEvent,
)
import acecqa_agent.api.main as api_main


client = TestClient(api_main.app)


def test_health_and_frontend() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == "0.6.0"

    frontend = client.get("/")
    assert frontend.status_code == 200
    assert "ACECQA Service Risk Copilot" in frontend.text


def test_system_info_exposes_stable_product_snapshot() -> None:
    response = client.get("/api/system/info")
    assert response.status_code == 200
    payload = response.json()
    assert payload["service_records"] == 17663
    assert payload["policy_chunks"] == 1395
    assert payload["tool_count"] == 9
    assert payload["risk_thresholds"]["capacity_p25_places"] == 40.0
    assert payload["evaluation"]["ready"] is True
    assert payload["evaluation"]["cases"] == 50
    assert payload["evaluation"]["passed"] == 50


def test_service_profile_endpoint_and_not_found() -> None:
    response = client.get("/api/services/SE-40000427")
    assert response.status_code == 200
    profile = response.json()["profile"]
    assert profile["service_name"] == "Napranum Early Childhood Centre"
    assert profile["state"] == "QLD"

    missing = client.get("/api/services/SE-99999999")
    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "SERVICE_NOT_FOUND"


def test_scenario_endpoint_reproduces_regression() -> None:
    response = client.post(
        "/api/scenario",
        json={"transport_percentile": 0.80, "capacity_percentile": 0.25},
    )
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["baseline"]["priority_service_count"] == 162
    assert result["scenario"]["priority_service_count"] == 149
    assert result["change_count"] == -13
    assert abs(result["scenario_thresholds"]["transport_cutoff_km"] - 6.744341249608515) < 1e-9


def test_policy_search_endpoint_uses_local_corpus() -> None:
    response = client.post(
        "/api/policy/search",
        json={
            "query": "What should a regulatory authority consider when responding to compliance?",
            "topic": "proportionality",
            "top_k": 3,
        },
    )
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["corpus_chunk_count"] == 1395
    assert result["result_count"] > 0
    assert all(item["source_url"].startswith("https://www.acecqa.gov.au/") for item in result["results"])


def test_chat_endpoint_serialises_agent_report(monkeypatch) -> None:
    report = AgentRunReport(
        query="How many rural Centre-Based Care services are in Queensland?",
        model="test-model",
        answer=GroundedAgentAnswer(
            answer="There are 227 services.",
            evidence=[
                GroundedEvidence(
                    source_tool="search_services",
                    claim="QLD rural Centre-Based Care search matched 227 services.",
                )
            ],
            methodology=["Used deterministic service filters."],
            limitations=[],
        ),
        used_tools=["search_services"],
        tool_trace=[
            ToolTraceEvent(
                sequence=1,
                event_type="tool_call",
                tool_name="search_services",
                arguments={"state": "QLD", "urban_rural": "Rural"},
            )
        ],
        policy_sources=[],
        usage=AgentUsageSummary(requests=2, input_tokens=100, output_tokens=20, total_tokens=120),
        latency_ms=1234.0,
    )

    monkeypatch.setattr(api_main, "run_copilot", lambda *args, **kwargs: report)
    response = client.post(
        "/api/chat",
        json={"message": report.query, "strict_grounding": True},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "There are 227 services."
    assert payload["used_tools"] == ["search_services"]
    assert payload["grounding_status"] == "tool_grounded"
    assert payload["usage"]["total_tokens"] == 120
