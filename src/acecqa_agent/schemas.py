from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

StateCode = Literal["ACT", "NSW", "NT", "QLD", "SA", "TAS", "VIC", "WA"]
UrbanRural = Literal["Urban", "Rural"]
ServiceType = Literal["Centre-Based Care", "Family Day Care"]


class ServiceFilters(BaseModel):
    state: StateCode | None = None
    urban_rural: UrbanRural | None = None
    service_type: ServiceType | None = None
    overall_rating: str | None = None


class SearchServicesInput(ServiceFilters):
    limit: int = Field(default=20, ge=1, le=100)


class ServiceSummary(BaseModel):
    service_approval_number: str
    service_name: str | None = None
    state: str | None = None
    urban_rural: str | None = None
    service_type: str | None = None
    overall_rating: str | None = None
    number_of_approved_places: float | None = None
    nearest_public_transport_km: float | None = None


class SearchServicesOutput(BaseModel):
    matched_count: int
    returned_count: int
    filters: ServiceFilters
    services: list[ServiceSummary]


class GetServiceProfileInput(BaseModel):
    service_approval_number: str = Field(min_length=1)


class ServiceProfile(BaseModel):
    service_approval_number: str
    service_name: str | None = None
    provider_legal_name: str | None = None
    service_type: str | None = None
    state: str | None = None
    suburb: str | None = None
    postcode: str | None = None
    urban_rural: str | None = None
    overall_rating: str | None = None
    number_of_approved_places: float | None = None
    nearest_public_transport_km: float | None = None
    distance_to_train_station_km: float | None = None
    distance_to_bus_station_km: float | None = None
    longitude: float | None = None
    latitude: float | None = None
    valid_spatial_record: bool | None = None


class CalculateRiskInput(BaseModel):
    service_approval_number: str = Field(min_length=1)


class RiskThresholds(BaseModel):
    transport_p75_km: float
    capacity_p25_places: float
    scope: str


class RiskAssessment(BaseModel):
    service_approval_number: str
    service_name: str | None = None
    eligible_for_risk_scoring: bool
    gap_score: int | None = Field(default=None, ge=0, le=3)
    gap_label: str | None = None
    poor_access_flag: bool | None = None
    weak_quality_flag: bool | None = None
    low_capacity_flag: bool | None = None
    nearest_public_transport_km: float | None = None
    overall_rating: str | None = None
    number_of_approved_places: float | None = None
    thresholds: RiskThresholds
    limitations: list[str] = Field(default_factory=list)


class FindHighRiskInput(ServiceFilters):
    top_k: int = Field(default=20, ge=1, le=100)
    minimum_gap_score: int = Field(default=2, ge=0, le=3)


class RankedRiskService(ServiceSummary):
    rank: int
    gap_score: int
    gap_label: str
    poor_access_flag: bool
    weak_quality_flag: bool
    low_capacity_flag: bool


class FindHighRiskOutput(BaseModel):
    matched_count: int
    returned_count: int
    ranking_policy: str
    thresholds: RiskThresholds
    services: list[RankedRiskService]


class CompareTransportAccessInput(BaseModel):
    state: StateCode | None = None
    service_type: ServiceType | None = None
    group_by: Literal["urban_rural", "state", "service_type"] = "urban_rural"


class TransportGroupSummary(BaseModel):
    group: str
    service_count: int
    median_nearest_transport_km: float | None = None
    mean_nearest_transport_km: float | None = None
    p75_nearest_transport_km: float | None = None


class CompareTransportAccessOutput(BaseModel):
    group_by: str
    filters: ServiceFilters
    groups: list[TransportGroupSummary]


class AnalyseQuartileOutcomesInput(BaseModel):
    state: StateCode | None = None
    urban_rural: UrbanRural | None = None
    service_type: ServiceType = "Centre-Based Care"
    min_group_size: int = Field(default=20, ge=1)


class QuartileOutcomeSummary(BaseModel):
    transport_access_quartile: str
    service_count: int
    below_meeting_rate: float | None = None
    approved_places_non_missing: int
    median_approved_places: float | None = None
    mean_approved_places: float | None = None


class AnalyseQuartileOutcomesOutput(BaseModel):
    filters: ServiceFilters
    min_group_size: int
    caveat: str
    quartiles: list[QuartileOutcomeSummary]
