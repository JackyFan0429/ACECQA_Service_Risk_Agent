"""Agent-facing adapters for the deterministic analytics tools.

This module deliberately has no dependency on the OpenAI Agents SDK. It owns the
stable contract between an LLM runtime and the analytics layer: tool metadata,
Pydantic validation, deterministic invocation, and JSON-safe success/error envelopes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel, ValidationError

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
from acecqa_agent.tools import (
    analyse_transport_quartile_outcomes,
    calculate_risk_score,
    compare_transport_access,
    find_high_risk_services,
    get_service_profile,
    search_services,
)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    function: Callable[[Any], BaseModel]


TOOL_SPECS: dict[str, ToolSpec] = {
    "search_services": ToolSpec(
        name="search_services",
        description=(
            "Filter or count services by state, urban/rural classification, service type, or exact "
            "overall NQS rating. Use this for factual lookup/listing questions. Do NOT use it to rank "
            "regulatory risk; use find_high_risk_services for prioritisation."
        ),
        input_model=SearchServicesInput,
        output_model=SearchServicesOutput,
        function=search_services,
    ),
    "get_service_profile": ToolSpec(
        name="get_service_profile",
        description=(
            "Return decision-relevant fields for one exact service approval number, including location, "
            "NQS rating, authorised capacity, and transport distances."
        ),
        input_model=GetServiceProfileInput,
        output_model=ServiceProfile,
        function=get_service_profile,
    ),
    "calculate_risk_score": ToolSpec(
        name="calculate_risk_score",
        description=(
            "Calculate the validated v1 three-gap risk assessment for one service approval number. "
            "Returns eligibility, the 0-3 gap score, component flags, thresholds, and limitations."
        ),
        input_model=CalculateRiskInput,
        output_model=RiskAssessment,
        function=calculate_risk_score,
    ),
    "find_high_risk_services": ToolSpec(
        name="find_high_risk_services",
        description=(
            "Rank Centre-Based Care services for regulatory prioritisation using the deterministic v1 "
            "risk model. Use this when the user asks which services are highest risk, should be investigated "
            "first, or requests a priority/top-k list. If no top_k is specified, use 20. For the phrase "
            "highest-risk without another threshold, use minimum_gap_score=3 (triple-gap); use 2 for a broader "
            "high-risk candidate pool."
        ),
        input_model=FindHighRiskInput,
        output_model=FindHighRiskOutput,
        function=find_high_risk_services,
    ),
    "compare_transport_access": ToolSpec(
        name="compare_transport_access",
        description=(
            "Compare aggregate public-transport access statistics across urban/rural groups, states, or "
            "service types, optionally filtered by state or service type."
        ),
        input_model=CompareTransportAccessInput,
        output_model=CompareTransportAccessOutput,
        function=compare_transport_access,
    ),
    "analyse_transport_quartile_outcomes": ToolSpec(
        name="analyse_transport_quartile_outcomes",
        description=(
            "Analyse NQS quality outcomes and authorised capacity across transport-access quartiles Q1-Q4. "
            "Use this for questions about whether poorer transport access is associated with quality or "
            "capacity patterns. It does not establish unmet demand or causality."
        ),
        input_model=AnalyseQuartileOutcomesInput,
        output_model=AnalyseQuartileOutcomesOutput,
        function=analyse_transport_quartile_outcomes,
    ),
}


def _json_safe(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    return value


def invoke_registered_tool(tool_name: str, arguments: str | dict[str, Any]) -> dict[str, Any]:
    """Validate and execute one deterministic tool.

    Tool errors are returned as data rather than allowed to crash the agent loop. This
    gives the model a chance to recover from a bad parameter or an out-of-scope request.
    """
    spec = TOOL_SPECS.get(tool_name)
    if spec is None:
        return {
            "ok": False,
            "tool": tool_name,
            "error_type": "UnknownToolError",
            "message": f"Unknown tool: {tool_name}",
        }

    try:
        if isinstance(arguments, str):
            params = spec.input_model.model_validate_json(arguments)
        else:
            params = spec.input_model.model_validate(arguments)
        result = spec.function(params)
        return {
            "ok": True,
            "tool": tool_name,
            "data": _json_safe(result),
        }
    except ValidationError as exc:
        return {
            "ok": False,
            "tool": tool_name,
            "error_type": "ValidationError",
            "message": "Tool parameters failed schema validation.",
            "details": exc.errors(include_url=False),
        }
    except ValueError as exc:
        return {
            "ok": False,
            "tool": tool_name,
            "error_type": type(exc).__name__,
            "message": str(exc),
        }
    except Exception as exc:  # pragma: no cover - defensive production boundary
        return {
            "ok": False,
            "tool": tool_name,
            "error_type": type(exc).__name__,
            "message": "The deterministic analytics tool failed unexpectedly.",
        }


def invoke_registered_tool_json(tool_name: str, arguments: str | dict[str, Any]) -> str:
    """Return a compact JSON string suitable for feeding back to an LLM runtime."""
    return json.dumps(invoke_registered_tool(tool_name, arguments), ensure_ascii=False, separators=(",", ":"))
