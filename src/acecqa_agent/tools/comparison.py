from __future__ import annotations

import pandas as pd

from acecqa_agent.data_repository import get_repository
from acecqa_agent.schemas import (
    AnalyseQuartileOutcomesInput,
    AnalyseQuartileOutcomesOutput,
    CompareTransportAccessInput,
    CompareTransportAccessOutput,
    QuartileOutcomeSummary,
    ServiceFilters,
    TransportGroupSummary,
)
from .common import apply_filters, clean_value


def compare_transport_access(params: CompareTransportAccessInput) -> CompareTransportAccessOutput:
    """Compare deterministic transport-access statistics across a requested grouping."""
    filters = ServiceFilters(state=params.state, service_type=params.service_type)
    df = apply_filters(get_repository().analysis_services, filters)
    grouped = (
        df.groupby(params.group_by, observed=True)["nearest_public_transport_km"]
        .agg(["size", "median", "mean", lambda s: s.quantile(0.75)])
        .reset_index()
    )
    grouped.columns = [params.group_by, "service_count", "median", "mean", "p75"]
    groups = [
        TransportGroupSummary(
            group=str(row[params.group_by]),
            service_count=int(row["service_count"]),
            median_nearest_transport_km=clean_value(row["median"]),
            mean_nearest_transport_km=clean_value(row["mean"]),
            p75_nearest_transport_km=clean_value(row["p75"]),
        )
        for _, row in grouped.iterrows()
    ]
    return CompareTransportAccessOutput(group_by=params.group_by, filters=filters, groups=groups)


def analyse_transport_quartile_outcomes(params: AnalyseQuartileOutcomesInput) -> AnalyseQuartileOutcomesOutput:
    """Summarise quality and authorised capacity across transport-access quartiles."""
    filters = ServiceFilters(
        state=params.state,
        urban_rural=params.urban_rural,
        service_type=params.service_type,
    )
    df = apply_filters(get_repository().analysis_services, filters)
    rows = []
    for quartile, group in df.groupby("transport_access_quartile", observed=True):
        count = len(group)
        capacity = group["number_of_approved_places"]
        below_rate = group["below_meeting_flag"].mean()
        # Match the notebook's quality chart guard against unstable small groups.
        if count < params.min_group_size:
            below_rate = None
        rows.append(
            QuartileOutcomeSummary(
                transport_access_quartile=str(quartile),
                service_count=count,
                below_meeting_rate=clean_value(below_rate),
                approved_places_non_missing=int(capacity.notna().sum()),
                median_approved_places=clean_value(capacity.median()),
                mean_approved_places=clean_value(capacity.mean()),
            )
        )

    order = {"Q1 Closest": 1, "Q2": 2, "Q3": 3, "Q4 Farthest": 4}
    rows.sort(key=lambda x: order.get(x.transport_access_quartile, 99))
    return AnalyseQuartileOutcomesOutput(
        filters=filters,
        min_group_size=params.min_group_size,
        caveat=(
            "Approved places are authorised capacity only. They do not establish actual demand, "
            "enrolment, waitlists, utilisation, or unmet need."
        ),
        quartiles=rows,
    )
