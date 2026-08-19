"""Deterministic scenario analysis for the validated Centre-Based Care risk model.

Percentile thresholds are always computed from the same national validated Centre-Based
Care risk sample used by the v1 model. State/urban-rural filters change only the population
whose impact is reported; they never redefine the percentile thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from acecqa_agent.data_repository import get_repository
from acecqa_agent.schemas import (
    CompareRiskScenariosInput,
    CompareRiskScenariosOutput,
    RiskScenarioDefinition,
    ScenarioABGroupImpact,
    ScenarioChangedService,
    ScenarioComparisonSide,
    ScenarioGroupImpact,
    ScenarioPoolSummary,
    ScenarioScope,
    ScenarioThresholds,
    SimulateRiskThresholdsInput,
    SimulateRiskThresholdsOutput,
)
from .common import clean_value


BASELINE_TRANSPORT_PERCENTILE = 0.75
BASELINE_CAPACITY_PERCENTILE = 0.25
THRESHOLD_SCOPE = (
    "National validated Centre-Based Care risk sample with non-missing approved places; "
    "subgroup filters do not redefine percentile thresholds."
)
CAVEAT = (
    "Scenario results are sensitivity analysis for a prioritisation screen. They do not show "
    "causal effects, optimal policy thresholds, unmet demand, legal non-compliance, or an "
    "automatic basis for enforcement."
)


@dataclass(frozen=True)
class _EvaluatedScenario:
    definition: RiskScenarioDefinition
    thresholds: ScenarioThresholds
    frame: pd.DataFrame


def _thresholds(df: pd.DataFrame, definition: RiskScenarioDefinition) -> ScenarioThresholds:
    transport_cutoff = float(
        df["nearest_public_transport_km"].quantile(definition.transport_percentile)
    )
    capacity_cutoff = float(
        df["number_of_approved_places"].quantile(definition.capacity_percentile)
    )
    return ScenarioThresholds(
        transport_percentile=definition.transport_percentile,
        transport_cutoff_km=transport_cutoff,
        capacity_percentile=definition.capacity_percentile,
        capacity_cutoff_places=capacity_cutoff,
        minimum_gap_score=definition.minimum_gap_score,
        threshold_scope=THRESHOLD_SCOPE,
    )


def _evaluate(definition: RiskScenarioDefinition) -> _EvaluatedScenario:
    repo = get_repository()
    national = repo.risk_services
    thresholds = _thresholds(national, definition)
    frame = national.copy()
    frame["scenario_poor_access_flag"] = frame["nearest_public_transport_km"].ge(
        thresholds.transport_cutoff_km
    )
    frame["scenario_weak_quality_flag"] = frame["overall_rating_binary"].eq("Below Meeting NQS")
    frame["scenario_low_capacity_flag"] = frame["number_of_approved_places"].le(
        thresholds.capacity_cutoff_places
    )
    frame["scenario_gap_score"] = (
        frame["scenario_poor_access_flag"].astype(int)
        + frame["scenario_weak_quality_flag"].astype(int)
        + frame["scenario_low_capacity_flag"].astype(int)
    )
    frame["scenario_priority_flag"] = frame["scenario_gap_score"].ge(definition.minimum_gap_score)
    return _EvaluatedScenario(definition=definition, thresholds=thresholds, frame=frame)


def _filter_scope(df: pd.DataFrame, scope: ScenarioScope) -> pd.DataFrame:
    result = df
    if scope.state is not None:
        result = result.loc[result["state"].eq(scope.state)]
    if scope.urban_rural is not None:
        result = result.loc[result["urban_rural"].eq(scope.urban_rural)]
    return result.copy()


def _pool_summary(df: pd.DataFrame) -> ScenarioPoolSummary:
    eligible = len(df)
    priority = int(df["scenario_priority_flag"].sum()) if eligible else 0
    rate = priority / eligible if eligible else 0.0
    return ScenarioPoolSummary(
        eligible_service_count=eligible,
        priority_service_count=priority,
        priority_rate=rate,
    )


def _percent_change(new: int, old: int) -> float | None:
    if old == 0:
        return None
    return (new - old) / old * 100.0


def _changed_service(row: pd.Series) -> ScenarioChangedService:
    return ScenarioChangedService(
        service_approval_number=str(row["service_approval_number"]),
        service_name=clean_value(row.get("service_name")),
        state=clean_value(row.get("state")),
        urban_rural=clean_value(row.get("urban_rural")),
        overall_rating=clean_value(row.get("overall_rating")),
        number_of_approved_places=clean_value(row.get("number_of_approved_places")),
        nearest_public_transport_km=clean_value(row.get("nearest_public_transport_km")),
    )


def _sample_services(df: pd.DataFrame, ids: set[str], limit: int) -> list[ScenarioChangedService]:
    if limit <= 0 or not ids:
        return []
    selected = df.loc[df["service_approval_number"].astype("string").isin(ids)].copy()
    selected = selected.sort_values(
        ["nearest_public_transport_km", "number_of_approved_places", "service_approval_number"],
        ascending=[False, True, True],
    ).head(limit)
    return [_changed_service(row) for _, row in selected.iterrows()]


def _group_impacts(
    baseline: pd.DataFrame,
    scenario: pd.DataFrame,
    group_col: str,
) -> list[ScenarioGroupImpact]:
    groups = sorted(set(baseline[group_col].dropna().astype(str)) | set(scenario[group_col].dropna().astype(str)))
    results: list[ScenarioGroupImpact] = []
    for group in groups:
        base_g = baseline.loc[baseline[group_col].astype("string").eq(group)]
        scen_g = scenario.loc[scenario[group_col].astype("string").eq(group)]
        base_count = int(base_g["scenario_priority_flag"].sum())
        scen_count = int(scen_g["scenario_priority_flag"].sum())
        results.append(
            ScenarioGroupImpact(
                group=group,
                eligible_service_count=len(scen_g),
                baseline_priority_count=base_count,
                scenario_priority_count=scen_count,
                change_count=scen_count - base_count,
                change_percent=_percent_change(scen_count, base_count),
            )
        )
    return results


def simulate_risk_thresholds(params: SimulateRiskThresholdsInput) -> SimulateRiskThresholdsOutput:
    """Compare one proposed percentile scenario with the fixed P75/P25 v1 baseline."""
    scope = ScenarioScope(state=params.state, urban_rural=params.urban_rural)
    baseline_def = RiskScenarioDefinition(
        label="Baseline P75/P25",
        transport_percentile=BASELINE_TRANSPORT_PERCENTILE,
        capacity_percentile=BASELINE_CAPACITY_PERCENTILE,
        minimum_gap_score=params.minimum_gap_score,
    )
    scenario_def = RiskScenarioDefinition(
        label="Scenario",
        transport_percentile=params.transport_percentile,
        capacity_percentile=params.capacity_percentile,
        minimum_gap_score=params.minimum_gap_score,
    )
    baseline_eval = _evaluate(baseline_def)
    scenario_eval = _evaluate(scenario_def)
    baseline = _filter_scope(baseline_eval.frame, scope)
    scenario = _filter_scope(scenario_eval.frame, scope)

    base_ids = set(
        baseline.loc[baseline["scenario_priority_flag"], "service_approval_number"].astype(str)
    )
    scenario_ids = set(
        scenario.loc[scenario["scenario_priority_flag"], "service_approval_number"].astype(str)
    )
    added = scenario_ids - base_ids
    removed = base_ids - scenario_ids
    base_summary = _pool_summary(baseline)
    scenario_summary = _pool_summary(scenario)

    return SimulateRiskThresholdsOutput(
        scope=scope,
        baseline_thresholds=baseline_eval.thresholds,
        scenario_thresholds=scenario_eval.thresholds,
        baseline=base_summary,
        scenario=scenario_summary,
        change_count=scenario_summary.priority_service_count - base_summary.priority_service_count,
        change_percent=_percent_change(
            scenario_summary.priority_service_count, base_summary.priority_service_count
        ),
        overlap_count=len(base_ids & scenario_ids),
        added_count=len(added),
        removed_count=len(removed),
        added_services=_sample_services(scenario, added, params.changed_service_limit),
        removed_services=_sample_services(baseline, removed, params.changed_service_limit),
        by_state=_group_impacts(baseline, scenario, "state"),
        by_urban_rural=_group_impacts(baseline, scenario, "urban_rural"),
        interpretation_caveat=CAVEAT,
    )


def _ab_group_impacts(a: pd.DataFrame, b: pd.DataFrame, group_col: str) -> list[ScenarioABGroupImpact]:
    groups = sorted(set(a[group_col].dropna().astype(str)) | set(b[group_col].dropna().astype(str)))
    results: list[ScenarioABGroupImpact] = []
    for group in groups:
        a_g = a.loc[a[group_col].astype("string").eq(group)]
        b_g = b.loc[b[group_col].astype("string").eq(group)]
        a_count = int(a_g["scenario_priority_flag"].sum())
        b_count = int(b_g["scenario_priority_flag"].sum())
        results.append(
            ScenarioABGroupImpact(
                group=group,
                eligible_service_count=len(b_g),
                scenario_a_priority_count=a_count,
                scenario_b_priority_count=b_count,
                b_minus_a_count=b_count - a_count,
                b_vs_a_percent_change=_percent_change(b_count, a_count),
            )
        )
    return results


def compare_risk_scenarios(params: CompareRiskScenariosInput) -> CompareRiskScenariosOutput:
    """Compare two arbitrary deterministic percentile scenarios on the same validated sample."""
    scope = ScenarioScope(state=params.state, urban_rural=params.urban_rural)
    a_eval = _evaluate(params.scenario_a)
    b_eval = _evaluate(params.scenario_b)
    a = _filter_scope(a_eval.frame, scope)
    b = _filter_scope(b_eval.frame, scope)
    a_summary = _pool_summary(a)
    b_summary = _pool_summary(b)

    a_ids = set(a.loc[a["scenario_priority_flag"], "service_approval_number"].astype(str))
    b_ids = set(b.loc[b["scenario_priority_flag"], "service_approval_number"].astype(str))
    only_a = a_ids - b_ids
    only_b = b_ids - a_ids

    return CompareRiskScenariosOutput(
        scope=scope,
        scenario_a=ScenarioComparisonSide(
            label=params.scenario_a.label,
            thresholds=a_eval.thresholds,
            pool=a_summary,
        ),
        scenario_b=ScenarioComparisonSide(
            label=params.scenario_b.label,
            thresholds=b_eval.thresholds,
            pool=b_summary,
        ),
        b_minus_a_count=b_summary.priority_service_count - a_summary.priority_service_count,
        b_vs_a_percent_change=_percent_change(
            b_summary.priority_service_count, a_summary.priority_service_count
        ),
        overlap_count=len(a_ids & b_ids),
        only_a_count=len(only_a),
        only_b_count=len(only_b),
        only_a_services=_sample_services(a, only_a, params.changed_service_limit),
        only_b_services=_sample_services(b, only_b, params.changed_service_limit),
        by_state=_ab_group_impacts(a, b, "state"),
        by_urban_rural=_ab_group_impacts(a, b, "urban_rural"),
        interpretation_caveat=CAVEAT,
    )
