import pytest

from acecqa_agent.agent.tool_adapter import invoke_registered_tool
from acecqa_agent.schemas import (
    CompareRiskScenariosInput,
    RiskScenarioDefinition,
    SimulateRiskThresholdsInput,
)
from acecqa_agent.tools.scenario_analysis import compare_risk_scenarios, simulate_risk_thresholds


def test_baseline_scenario_reproduces_v1_triple_gap_count():
    result = simulate_risk_thresholds(
        SimulateRiskThresholdsInput(
            transport_percentile=0.75,
            capacity_percentile=0.25,
            minimum_gap_score=3,
        )
    )
    assert result.baseline.priority_service_count == 162
    assert result.scenario.priority_service_count == 162
    assert result.change_count == 0
    assert result.added_count == 0
    assert result.removed_count == 0
    assert result.scenario_thresholds.transport_cutoff_km == pytest.approx(5.329340006807538)
    assert result.scenario_thresholds.capacity_cutoff_places == pytest.approx(40.0)


def test_p80_transport_scenario_reduces_national_triple_gap_pool():
    result = simulate_risk_thresholds(
        SimulateRiskThresholdsInput(
            transport_percentile=0.80,
            capacity_percentile=0.25,
            minimum_gap_score=3,
        )
    )
    assert result.baseline.priority_service_count == 162
    assert result.scenario.priority_service_count == 149
    assert result.change_count == -13
    assert result.added_count == 0
    assert result.removed_count == 13
    assert result.scenario_thresholds.transport_cutoff_km == pytest.approx(6.744341249608515)


def test_qld_rural_scope_does_not_redefine_national_thresholds():
    result = simulate_risk_thresholds(
        SimulateRiskThresholdsInput(
            state="QLD",
            urban_rural="Rural",
            transport_percentile=0.80,
            capacity_percentile=0.25,
            minimum_gap_score=3,
        )
    )
    assert result.baseline.eligible_service_count == 193
    assert result.baseline.priority_service_count == 21
    assert result.scenario.priority_service_count == 20
    assert result.change_count == -1
    assert result.scenario_thresholds.transport_cutoff_km == pytest.approx(6.744341249608515)
    assert [item.group for item in result.by_state] == ["QLD"]
    assert [item.group for item in result.by_urban_rural] == ["Rural"]


def test_compare_broad_vs_strict_scenarios():
    result = compare_risk_scenarios(
        CompareRiskScenariosInput(
            scenario_a=RiskScenarioDefinition(
                label="Broad",
                transport_percentile=0.70,
                capacity_percentile=0.30,
                minimum_gap_score=3,
            ),
            scenario_b=RiskScenarioDefinition(
                label="Strict",
                transport_percentile=0.85,
                capacity_percentile=0.20,
                minimum_gap_score=3,
            ),
        )
    )
    assert result.scenario_a.pool.priority_service_count == 196
    assert result.scenario_b.pool.priority_service_count == 111
    assert result.b_minus_a_count == -85
    assert result.only_a_count == 85
    assert result.only_b_count == 0
    assert result.overlap_count == 111


def test_scenario_adapter_returns_machine_readable_output():
    result = invoke_registered_tool(
        "simulate_risk_thresholds",
        {
            "transport_percentile": 0.80,
            "capacity_percentile": 0.25,
            "minimum_gap_score": 3,
            "changed_service_limit": 3,
        },
    )
    assert result["ok"] is True
    assert result["data"]["scenario"]["priority_service_count"] == 149
    assert len(result["data"]["removed_services"]) == 3


def test_scenario_adapter_rejects_invalid_percentile():
    result = invoke_registered_tool(
        "simulate_risk_thresholds",
        {
            "transport_percentile": 80,
            "capacity_percentile": 0.25,
        },
    )
    assert result["ok"] is False
    assert result["error_type"] == "ValidationError"
