import json
from pathlib import Path

from acecqa_agent.schemas import (
    AnalyseQuartileOutcomesInput,
    AnalyseQuartileOutcomesOutput,
    CalculateRiskInput,
    CompareTransportAccessInput,
    CompareTransportAccessOutput,
    FindHighRiskInput,
    FindHighRiskOutput,
    GetServiceProfileInput,
    RiskAssessment,
    SearchServicesInput,
    SearchServicesOutput,
    ServiceProfile,
)

TOOLS = {
    "search_services": (SearchServicesInput, SearchServicesOutput),
    "get_service_profile": (GetServiceProfileInput, ServiceProfile),
    "calculate_risk_score": (CalculateRiskInput, RiskAssessment),
    "find_high_risk_services": (FindHighRiskInput, FindHighRiskOutput),
    "compare_transport_access": (CompareTransportAccessInput, CompareTransportAccessOutput),
    "analyse_transport_quartile_outcomes": (AnalyseQuartileOutcomesInput, AnalyseQuartileOutcomesOutput),
}

payload = {
    name: {
        "input_schema": input_model.model_json_schema(),
        "output_schema": output_model.model_json_schema(),
    }
    for name, (input_model, output_model) in TOOLS.items()
}

out = Path(__file__).parent / "docs" / "tool_schemas.json"
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(out)
