from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from acecqa_agent.agent.runtime import (
    AgentUsageSummary,
    GroundedEvidence,
    PolicySourceCitation,
    ToolTraceEvent,
)
from acecqa_agent.schemas import (
    PolicySearchOutput,
    ServiceProfile,
    SimulateRiskThresholdsOutput,
    StateCode,
    UrbanRural,
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=4000)
    model: str | None = None
    strict_grounding: bool = Field(
        default=False,
        description=(
            "If true, reject responses that do not call a deterministic tool. Product mode "
            "defaults to false so explicit uncertainty/boundary answers can be returned."
        ),
    )


class ChatResponse(BaseModel):
    answer: str
    evidence: list[GroundedEvidence]
    policy_sources: list[PolicySourceCitation]
    methodology: list[str]
    limitations: list[str]
    used_tools: list[str]
    tool_trace: list[ToolTraceEvent]
    usage: AgentUsageSummary
    latency_ms: float
    model: str
    grounding_status: Literal["tool_grounded", "boundary_no_tool"]


class ScenarioRequest(BaseModel):
    transport_percentile: float = Field(default=0.80, ge=0.50, le=0.95)
    capacity_percentile: float = Field(default=0.25, ge=0.05, le=0.50)
    minimum_gap_score: int = Field(default=3, ge=2, le=3)
    state: StateCode | None = None
    urban_rural: UrbanRural | None = None
    changed_service_limit: int = Field(default=10, ge=0, le=50)


class PolicySearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    topic: str | None = None
    top_k: int = Field(default=5, ge=1, le=8)


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str
    version: str


class EvaluationSnapshot(BaseModel):
    benchmark_version: str | None = None
    cases: int | None = None
    passed: int | None = None
    task_success_rate: float | None = None
    tool_selection_accuracy: float | None = None
    parameter_accuracy: float | None = None
    numerical_accuracy: float | None = None
    policy_grounding_rate: float | None = None
    boundary_handling_rate: float | None = None
    avg_tokens_per_query: float | None = None
    avg_latency_ms: float | None = None
    ready: bool = False


class SystemInfoResponse(BaseModel):
    service: str
    version: str
    model_default: str
    api_key_configured: bool
    service_records: int
    risk_eligible_records: int
    policy_chunks: int
    tool_count: int
    tools: list[str]
    risk_thresholds: dict[str, float]
    evaluation: EvaluationSnapshot
    architecture: list[str]


class ServiceProfileResponse(BaseModel):
    profile: ServiceProfile


class ScenarioResponse(BaseModel):
    result: SimulateRiskThresholdsOutput


class PolicyResponse(BaseModel):
    result: PolicySearchOutput


class ErrorDetail(BaseModel):
    code: str
    message: str
    partial_report: dict[str, Any] | None = None
