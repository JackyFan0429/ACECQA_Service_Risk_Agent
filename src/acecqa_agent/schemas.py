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

PolicyTopic = Literal[
    "nqf_overview",
    "legal_hierarchy",
    "guide_updates",
    "nqs",
    "quality_areas",
    "quality_ratings",
    "assessment_rating",
    "working_towards_nqs",
    "quality_improvement",
    "qip",
    "significant_improvement_required",
    "regulatory_powers",
    "monitoring",
    "enforcement",
    "proportionality",
    "risk",
    "compliance_tools",
    "good_regulatory_practice",
    "enforceable_undertakings",
    "acecqa_role",
    "national_regulations",
    "operational_requirements",
]


class PolicySearchInput(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    topic: PolicyTopic | None = None
    top_k: int = Field(default=5, ge=1, le=8)


class PolicySearchResult(BaseModel):
    chunk_id: str
    source_id: str
    source_title: str
    source_url: str
    source_kind: str
    authority_level: str
    section: str | None = None
    excerpt: str
    retrieval_score: float
    source_retrieved_at: str | None = None


class PolicySearchOutput(BaseModel):
    query: str
    topic: PolicyTopic | None = None
    corpus_chunk_count: int
    result_count: int
    results: list[PolicySearchResult]
    caveat: str

# ---------------------------------------------------------------------------
# Milestone 4: deterministic scenario analysis
# ---------------------------------------------------------------------------

class ScenarioScope(BaseModel):
    state: StateCode | None = None
    urban_rural: UrbanRural | None = None


class RiskScenarioDefinition(BaseModel):
    label: str = Field(default="Scenario", min_length=1, max_length=80)
    transport_percentile: float = Field(
        default=0.75,
        ge=0.50,
        le=0.95,
        description="National Centre-Based Care percentile as a decimal; 0.80 means P80.",
    )
    capacity_percentile: float = Field(
        default=0.25,
        ge=0.05,
        le=0.50,
        description="National Centre-Based Care percentile as a decimal; 0.20 means P20.",
    )
    minimum_gap_score: int = Field(
        default=3,
        ge=2,
        le=3,
        description="Minimum number of overlapping gaps required for the priority pool.",
    )


class ScenarioThresholds(BaseModel):
    transport_percentile: float
    transport_cutoff_km: float
    capacity_percentile: float
    capacity_cutoff_places: float
    minimum_gap_score: int
    threshold_scope: str


class ScenarioPoolSummary(BaseModel):
    eligible_service_count: int
    priority_service_count: int
    priority_rate: float


class ScenarioGroupImpact(BaseModel):
    group: str
    eligible_service_count: int
    baseline_priority_count: int
    scenario_priority_count: int
    change_count: int
    change_percent: float | None = None


class ScenarioChangedService(BaseModel):
    service_approval_number: str
    service_name: str | None = None
    state: str | None = None
    urban_rural: str | None = None
    overall_rating: str | None = None
    number_of_approved_places: float | None = None
    nearest_public_transport_km: float | None = None


class SimulateRiskThresholdsInput(ScenarioScope):
    transport_percentile: float = Field(default=0.80, ge=0.50, le=0.95)
    capacity_percentile: float = Field(default=0.25, ge=0.05, le=0.50)
    minimum_gap_score: int = Field(default=3, ge=2, le=3)
    changed_service_limit: int = Field(default=10, ge=0, le=50)


class SimulateRiskThresholdsOutput(BaseModel):
    scope: ScenarioScope
    baseline_thresholds: ScenarioThresholds
    scenario_thresholds: ScenarioThresholds
    baseline: ScenarioPoolSummary
    scenario: ScenarioPoolSummary
    change_count: int
    change_percent: float | None = None
    overlap_count: int
    added_count: int
    removed_count: int
    added_services: list[ScenarioChangedService]
    removed_services: list[ScenarioChangedService]
    by_state: list[ScenarioGroupImpact]
    by_urban_rural: list[ScenarioGroupImpact]
    interpretation_caveat: str


class CompareRiskScenariosInput(ScenarioScope):
    scenario_a: RiskScenarioDefinition
    scenario_b: RiskScenarioDefinition
    changed_service_limit: int = Field(default=10, ge=0, le=50)


class ScenarioComparisonSide(BaseModel):
    label: str
    thresholds: ScenarioThresholds
    pool: ScenarioPoolSummary


class ScenarioABGroupImpact(BaseModel):
    group: str
    eligible_service_count: int
    scenario_a_priority_count: int
    scenario_b_priority_count: int
    b_minus_a_count: int
    b_vs_a_percent_change: float | None = None


class CompareRiskScenariosOutput(BaseModel):
    scope: ScenarioScope
    scenario_a: ScenarioComparisonSide
    scenario_b: ScenarioComparisonSide
    b_minus_a_count: int
    b_vs_a_percent_change: float | None = None
    overlap_count: int
    only_a_count: int
    only_b_count: int
    only_a_services: list[ScenarioChangedService]
    only_b_services: list[ScenarioChangedService]
    by_state: list[ScenarioABGroupImpact]
    by_urban_rural: list[ScenarioABGroupImpact]
    interpretation_caveat: str
