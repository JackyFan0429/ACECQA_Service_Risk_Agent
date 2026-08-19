from __future__ import annotations

from acecqa_agent.data_repository import get_repository
from acecqa_agent.schemas import (
    CalculateRiskInput,
    FindHighRiskInput,
    FindHighRiskOutput,
    RankedRiskService,
    RiskAssessment,
    ServiceFilters,
)
from .common import apply_filters, clean_value, risk_thresholds


def calculate_risk_score(params: CalculateRiskInput) -> RiskAssessment:
    """Reproduce the assignment's three-gap risk definition for one service."""
    repo = get_repository()
    all_df = repo.all_services
    base_match = all_df.loc[all_df["service_approval_number"].astype("string").eq(params.service_approval_number)]
    if base_match.empty:
        raise ValueError(f"Unknown service_approval_number: {params.service_approval_number}")
    base = base_match.iloc[0]

    risk_match = repo.risk_services.loc[
        repo.risk_services["service_approval_number"].astype("string").eq(params.service_approval_number)
    ]
    if risk_match.empty:
        limitations = []
        if clean_value(base.get("service_type")) != "Centre-Based Care":
            limitations.append("Risk score v1 is defined only for Centre-Based Care.")
        if clean_value(base.get("number_of_approved_places")) is None:
            limitations.append("Approved places is missing, so the capacity gap cannot be assessed.")
        if clean_value(base.get("nearest_public_transport_km")) is None:
            limitations.append("Valid public-transport distance is unavailable.")
        if clean_value(base.get("overall_rating_binary")) is None:
            limitations.append("A usable NQS overall rating is unavailable.")
        return RiskAssessment(
            service_approval_number=str(base["service_approval_number"]),
            service_name=clean_value(base.get("service_name")),
            eligible_for_risk_scoring=False,
            nearest_public_transport_km=clean_value(base.get("nearest_public_transport_km")),
            overall_rating=clean_value(base.get("overall_rating")),
            number_of_approved_places=clean_value(base.get("number_of_approved_places")),
            thresholds=risk_thresholds(),
            limitations=limitations or ["Service is outside the validated v1 risk-analysis scope."],
        )

    row = risk_match.iloc[0]
    return RiskAssessment(
        service_approval_number=str(row["service_approval_number"]),
        service_name=clean_value(row.get("service_name")),
        eligible_for_risk_scoring=True,
        gap_score=int(row["gap_score"]),
        gap_label=str(row["gap_label"]),
        poor_access_flag=bool(row["poor_access_flag"]),
        weak_quality_flag=bool(row["weak_quality_flag"]),
        low_capacity_flag=bool(row["low_capacity_flag"]),
        nearest_public_transport_km=clean_value(row.get("nearest_public_transport_km")),
        overall_rating=clean_value(row.get("overall_rating")),
        number_of_approved_places=clean_value(row.get("number_of_approved_places")),
        thresholds=risk_thresholds(),
        limitations=[
            "Approved places measure authorised capacity, not enrolment, waitlists, unmet demand, or local demand."
        ],
    )


def find_high_risk_services(params: FindHighRiskInput) -> FindHighRiskOutput:
    """Rank services without hidden LLM weighting.

    Ordering is lexicographic: gap score DESC, transport distance DESC, approved places ASC,
    then service approval number ASC for deterministic tie-breaking.
    """
    if params.service_type == "Family Day Care":
        raise ValueError(
            "Risk model v1 is validated only for Centre-Based Care; Family Day Care is outside scope."
        )

    repo = get_repository()
    filters = ServiceFilters(
        state=params.state,
        urban_rural=params.urban_rural,
        service_type=params.service_type or "Centre-Based Care",
        overall_rating=params.overall_rating,
    )
    df = apply_filters(repo.risk_services, filters)
    df = df.loc[df["gap_score"] >= params.minimum_gap_score].copy()
    df = df.sort_values(
        ["gap_score", "nearest_public_transport_km", "number_of_approved_places", "service_approval_number"],
        ascending=[False, False, True, True],
    )
    top = df.head(params.top_k)

    services = []
    for rank, (_, row) in enumerate(top.iterrows(), start=1):
        services.append(
            RankedRiskService(
                rank=rank,
                service_approval_number=str(row["service_approval_number"]),
                service_name=clean_value(row.get("service_name")),
                state=clean_value(row.get("state")),
                urban_rural=clean_value(row.get("urban_rural")),
                service_type=clean_value(row.get("service_type")),
                overall_rating=clean_value(row.get("overall_rating")),
                number_of_approved_places=clean_value(row.get("number_of_approved_places")),
                nearest_public_transport_km=clean_value(row.get("nearest_public_transport_km")),
                gap_score=int(row["gap_score"]),
                gap_label=str(row["gap_label"]),
                poor_access_flag=bool(row["poor_access_flag"]),
                weak_quality_flag=bool(row["weak_quality_flag"]),
                low_capacity_flag=bool(row["low_capacity_flag"]),
            )
        )

    return FindHighRiskOutput(
        matched_count=len(df),
        returned_count=len(services),
        ranking_policy=(
            "gap_score DESC; nearest_public_transport_km DESC; "
            "number_of_approved_places ASC; service_approval_number ASC"
        ),
        thresholds=risk_thresholds(),
        services=services,
    )
