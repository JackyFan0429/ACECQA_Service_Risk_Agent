from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from acecqa_agent.agent.runtime import AgentGroundingError, DEFAULT_MODEL, run_copilot
from acecqa_agent.agent.tool_registry import TOOL_REGISTRY
from acecqa_agent.api.schemas import (
    ChatRequest,
    ChatResponse,
    EvaluationSnapshot,
    HealthResponse,
    PolicyResponse,
    PolicySearchRequest,
    ScenarioRequest,
    ScenarioResponse,
    ServiceProfileResponse,
    SystemInfoResponse,
)
from acecqa_agent.config import PROJECT_ROOT
from acecqa_agent.data_repository import get_repository
from acecqa_agent.rag import get_policy_repository
from acecqa_agent.schemas import (
    GetServiceProfileInput,
    PolicySearchInput,
    SimulateRiskThresholdsInput,
)
from acecqa_agent.tools import get_service_profile, search_policy, simulate_risk_thresholds

APP_VERSION = "0.6.0"
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def _latest_ready_evaluation() -> EvaluationSnapshot:
    root = PROJECT_ROOT / "evals" / "m5_results"
    if not root.exists():
        return EvaluationSnapshot()

    candidates = sorted(root.glob("*/metrics*.json"), reverse=True)
    for path in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        acceptance = payload.get("acceptance", {}) or {}
        if payload.get("case_count") != 50 or acceptance.get("ready") is not True:
            continue
        dimensions = payload.get("dimensions", {}) or {}
        usage = payload.get("usage", {}) or {}
        return EvaluationSnapshot(
            benchmark_version="v1.1",
            cases=payload.get("case_count"),
            passed=payload.get("passed_cases"),
            task_success_rate=payload.get("task_success_rate"),
            tool_selection_accuracy=(dimensions.get("tool_selection", {}) or {}).get("accuracy"),
            parameter_accuracy=(dimensions.get("parameters", {}) or {}).get("accuracy"),
            numerical_accuracy=(dimensions.get("numerical", {}) or {}).get("accuracy"),
            policy_grounding_rate=(dimensions.get("policy_grounding", {}) or {}).get("accuracy"),
            boundary_handling_rate=payload.get("boundary_handling_rate"),
            avg_tokens_per_query=usage.get("avg_tokens_per_query"),
            avg_latency_ms=usage.get("avg_latency_ms"),
            ready=True,
        )
    return EvaluationSnapshot()


def _partial_error(exc: AgentGroundingError) -> dict[str, Any] | None:
    if exc.report is None:
        return None
    return exc.report.model_dump(mode="json")


def create_app() -> FastAPI:
    app = FastAPI(
        title="ACECQA Service Risk Copilot API",
        version=APP_VERSION,
        description=(
            "Portfolio-grade decision-support API exposing the evaluated ACECQA risk copilot, "
            "deterministic scenario analysis, policy retrieval, and service lookup."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        return HealthResponse(service="acecqa-risk-agent", version=APP_VERSION)

    @app.get("/api/system/info", response_model=SystemInfoResponse, tags=["system"])
    def system_info() -> SystemInfoResponse:
        repo = get_repository()
        policy_repo = get_policy_repository()
        return SystemInfoResponse(
            service="ACECQA Service Risk Copilot",
            version=APP_VERSION,
            model_default=os.getenv("ACECQA_AGENT_MODEL", DEFAULT_MODEL),
            api_key_configured=bool(os.getenv("OPENAI_API_KEY")),
            service_records=len(repo.all_services),
            risk_eligible_records=len(repo.risk_services),
            policy_chunks=policy_repo.chunk_count,
            tool_count=len(TOOL_REGISTRY),
            tools=list(TOOL_REGISTRY.keys()),
            risk_thresholds={
                "transport_p75_km": repo.poor_access_cutoff,
                "capacity_p25_places": repo.low_capacity_cutoff,
            },
            evaluation=_latest_ready_evaluation(),
            architecture=[
                "Single LLM agent for intent and orchestration",
                "Nine deterministic analytics/scenario/policy tools",
                "Local BM25 policy retrieval over a versioned official Guide snapshot",
                "Grounded evidence and policy chunk validation",
                "50-case formal evaluation harness",
            ],
        )

    @app.post("/api/chat", response_model=ChatResponse, tags=["agent"])
    def chat(request: ChatRequest) -> ChatResponse:
        try:
            report = run_copilot(
                request.message,
                model=request.model,
                require_tool=request.strict_grounding,
            )
        except AgentGroundingError as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "GROUNDING_REJECTED",
                    "message": str(exc),
                    "partial_report": _partial_error(exc),
                },
            ) from exc
        except RuntimeError as exc:
            message = str(exc)
            status = 503 if "OPENAI_API_KEY" in message else 500
            raise HTTPException(
                status_code=status,
                detail={"code": "AGENT_RUNTIME_ERROR", "message": message},
            ) from exc

        return ChatResponse(
            answer=report.answer.answer,
            evidence=report.answer.evidence,
            policy_sources=report.policy_sources,
            methodology=report.answer.methodology,
            limitations=report.answer.limitations,
            used_tools=report.used_tools,
            tool_trace=report.tool_trace,
            usage=report.usage,
            latency_ms=report.latency_ms,
            model=report.model,
            grounding_status="tool_grounded" if report.used_tools else "boundary_no_tool",
        )

    @app.get(
        "/api/services/{service_approval_number}",
        response_model=ServiceProfileResponse,
        tags=["deterministic"],
    )
    def service_profile(service_approval_number: str) -> ServiceProfileResponse:
        try:
            profile = get_service_profile(
                GetServiceProfileInput(service_approval_number=service_approval_number)
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=404,
                detail={"code": "SERVICE_NOT_FOUND", "message": str(exc)},
            ) from exc
        return ServiceProfileResponse(profile=profile)

    @app.post("/api/scenario", response_model=ScenarioResponse, tags=["deterministic"])
    def scenario(request: ScenarioRequest) -> ScenarioResponse:
        result = simulate_risk_thresholds(
            SimulateRiskThresholdsInput(**request.model_dump())
        )
        return ScenarioResponse(result=result)

    @app.post("/api/policy/search", response_model=PolicyResponse, tags=["deterministic"])
    def policy_search(request: PolicySearchRequest) -> PolicyResponse:
        try:
            params = PolicySearchInput(**request.model_dump())
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": "INVALID_POLICY_QUERY", "message": str(exc)},
            ) from exc
        return PolicyResponse(result=search_policy(params))

    if FRONTEND_DIR.exists():
        assets_dir = FRONTEND_DIR / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/", include_in_schema=False)
        def frontend() -> FileResponse:
            return FileResponse(FRONTEND_DIR / "index.html")

    return app


app = create_app()
