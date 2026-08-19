import math

from acecqa_agent.data_repository import get_repository
from acecqa_agent.schemas import (
    CalculateRiskInput,
    FindHighRiskInput,
    GetServiceProfileInput,
    SearchServicesInput,
)
from acecqa_agent.tools import calculate_risk_score, find_high_risk_services, get_service_profile, search_services


def test_dataset_and_notebook_risk_cutoffs_are_preserved():
    repo = get_repository()
    assert len(repo.all_services) == 17663
    assert math.isclose(repo.poor_access_cutoff, 5.329340006807538, rel_tol=1e-9)
    assert repo.low_capacity_cutoff == 40.0
    assert int((repo.risk_services["gap_score"] == 3).sum()) == 162


def test_qld_rural_search_count():
    result = search_services(
        SearchServicesInput(
            state="QLD",
            urban_rural="Rural",
            service_type="Centre-Based Care",
            limit=5,
        )
    )
    assert result.matched_count == 227
    assert result.returned_count == 5


def test_qld_rural_high_risk_ranking():
    result = find_high_risk_services(
        FindHighRiskInput(
            state="QLD",
            urban_rural="Rural",
            service_type="Centre-Based Care",
            minimum_gap_score=3,
            top_k=20,
        )
    )
    assert result.matched_count == 21
    assert result.services[0].service_approval_number == "SE-40000427"
    assert result.services[0].gap_score == 3


def test_single_service_risk_assessment():
    result = calculate_risk_score(CalculateRiskInput(service_approval_number="SE-40000427"))
    assert result.eligible_for_risk_scoring is True
    assert result.gap_score == 3
    assert result.poor_access_flag is True
    assert result.weak_quality_flag is True
    assert result.low_capacity_flag is True


def test_service_profile_normalises_postcode():
    result = get_service_profile(GetServiceProfileInput(service_approval_number="SE-40000427"))
    assert result.postcode == "4874"
