from acecqa_agent.schemas import FindHighRiskInput
from acecqa_agent.tools import find_high_risk_services


if __name__ == "__main__":
    result = find_high_risk_services(
        FindHighRiskInput(
            state="QLD",
            urban_rural="Rural",
            service_type="Centre-Based Care",
            top_k=20,
            minimum_gap_score=3,
        )
    )
    print(result.model_dump_json(indent=2))
