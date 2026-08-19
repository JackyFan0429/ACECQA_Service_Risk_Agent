from __future__ import annotations

from acecqa_agent.data_repository import get_repository
from acecqa_agent.schemas import (
    GetServiceProfileInput,
    SearchServicesInput,
    SearchServicesOutput,
    ServiceFilters,
    ServiceProfile,
    ServiceSummary,
)
from .common import apply_filters, clean_value


def _summary_from_row(row) -> ServiceSummary:
    return ServiceSummary(
        service_approval_number=str(row["service_approval_number"]),
        service_name=clean_value(row.get("service_name")),
        state=clean_value(row.get("state")),
        urban_rural=clean_value(row.get("urban_rural")),
        service_type=clean_value(row.get("service_type")),
        overall_rating=clean_value(row.get("overall_rating")),
        number_of_approved_places=clean_value(row.get("number_of_approved_places")),
        nearest_public_transport_km=clean_value(row.get("nearest_public_transport_km")),
    )


def search_services(params: SearchServicesInput) -> SearchServicesOutput:
    """Filter services using deterministic dataset fields; no LLM arithmetic or inference."""
    df = apply_filters(get_repository().all_services, params)
    rows = df.sort_values("service_approval_number").head(params.limit)
    filters = ServiceFilters(
        state=params.state,
        urban_rural=params.urban_rural,
        service_type=params.service_type,
        overall_rating=params.overall_rating,
    )
    return SearchServicesOutput(
        matched_count=len(df),
        returned_count=len(rows),
        filters=filters,
        services=[_summary_from_row(row) for _, row in rows.iterrows()],
    )


def get_service_profile(params: GetServiceProfileInput) -> ServiceProfile:
    """Return a single service's decision-relevant fields."""
    df = get_repository().all_services
    matches = df.loc[df["service_approval_number"].astype("string").eq(params.service_approval_number)]
    if matches.empty:
        raise ValueError(f"Unknown service_approval_number: {params.service_approval_number}")
    row = matches.iloc[0]
    return ServiceProfile(
        service_approval_number=str(row["service_approval_number"]),
        service_name=clean_value(row.get("service_name")),
        provider_legal_name=clean_value(row.get("provider_legal_name")),
        service_type=clean_value(row.get("service_type")),
        state=clean_value(row.get("state")),
        suburb=clean_value(row.get("suburb")),
        postcode=(
            None
            if clean_value(row.get("postcode")) is None
            else str(clean_value(row.get("postcode"))).replace(".0", "").zfill(4)
        ),
        urban_rural=clean_value(row.get("urban_rural")),
        overall_rating=clean_value(row.get("overall_rating")),
        number_of_approved_places=clean_value(row.get("number_of_approved_places")),
        nearest_public_transport_km=clean_value(row.get("nearest_public_transport_km")),
        distance_to_train_station_km=clean_value(row.get("distance_to_train_station_km")),
        distance_to_bus_station_km=clean_value(row.get("distance_to_bus_station_km")),
        longitude=clean_value(row.get("longitude")),
        latitude=clean_value(row.get("latitude")),
        valid_spatial_record=clean_value(row.get("valid_spatial_record")),
    )
