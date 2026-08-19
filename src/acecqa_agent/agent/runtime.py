"""Single-agent runtime for ACECQA Service Risk Copilot milestone 4."""

from __future__ import annotations

import json
import os
import time
from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, Field

from acecqa_agent.agent.openai_tools import build_openai_tools
from acecqa_agent.agent.system_prompt import SYSTEM_PROMPT

DEFAULT_MODEL = "gpt-5.6-terra"


AgentToolName = Literal[
    "search_services",
    "get_service_profile",
    "calculate_risk_score",
    "find_high_risk_services",
    "compare_transport_access",
    "analyse_transport_quartile_outcomes",
    "search_policy",
    "simulate_risk_thresholds",
    "compare_risk_scenarios",
]


class GroundedEvidence(BaseModel):
    source_tool: AgentToolName
    claim: str
    policy_chunk_ids: list[str] = Field(
        default_factory=list,
        description="For search_policy evidence, copy chunk_id values returned by that tool.",
    )


class PolicySourceCitation(BaseModel):
    chunk_id: str
    source_title: str
    source_url: str
    section: str | None = None
    authority_level: str | None = None


class GroundedAgentAnswer(BaseModel):
    answer: str = Field(description="Direct answer to the user's question. Markdown is allowed.")
    evidence: list[GroundedEvidence] = Field(
        default_factory=list,
        description="Important factual claims tied to tools called during this run.",
    )
    methodology: list[str] = Field(
        default_factory=list,
        description="Short explanation of deterministic method or ranking rule used.",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Data scope, interpretation, and policy limitations relevant to this answer.",
    )


class ToolTraceEvent(BaseModel):
    sequence: int
    event_type: str
    tool_name: str | None = None
    call_id: str | None = None
    arguments: Any | None = None
    output: Any | None = None


class AgentUsageSummary(BaseModel):
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class AgentRunReport(BaseModel):
    query: str
    model: str
    answer: GroundedAgentAnswer
    used_tools: list[str]
    tool_trace: list[ToolTraceEvent]
    policy_sources: list[PolicySourceCitation] = Field(default_factory=list)
    usage: AgentUsageSummary
    latency_ms: float


class AgentGroundingError(RuntimeError):
    """Grounding failure that may retain the completed model run for eval diagnostics."""

    def __init__(self, message: str, *, report: "AgentRunReport | None" = None):
        super().__init__(message)
        self.report = report


def _field(raw: Any, name: str) -> Any:
    if isinstance(raw, Mapping):
        return raw.get(name)
    return getattr(raw, name, None)


def _maybe_parse_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


def extract_tool_trace(new_items: list[Any]) -> list[ToolTraceEvent]:
    """Convert SDK run items into a small, stable audit trace for demos and evals."""
    trace: list[ToolTraceEvent] = []
    call_to_tool: dict[str, str] = {}

    for item in new_items:
        item_type = type(item).__name__
        raw = getattr(item, "raw_item", None)
        call_id = _field(raw, "call_id") or getattr(item, "call_id", None)

        if item_type == "ToolCallItem":
            name = _field(raw, "name") or getattr(item, "tool_name", None)
            arguments = _field(raw, "arguments")
            if call_id and name:
                call_to_tool[str(call_id)] = str(name)
            trace.append(
                ToolTraceEvent(
                    sequence=len(trace) + 1,
                    event_type="tool_call",
                    tool_name=None if name is None else str(name),
                    call_id=None if call_id is None else str(call_id),
                    arguments=_maybe_parse_json(arguments),
                )
            )
        elif item_type == "ToolCallOutputItem":
            name = call_to_tool.get(str(call_id)) if call_id is not None else None
            output = getattr(item, "output", None)
            trace.append(
                ToolTraceEvent(
                    sequence=len(trace) + 1,
                    event_type="tool_output",
                    tool_name=name,
                    call_id=None if call_id is None else str(call_id),
                    output=_maybe_parse_json(output),
                )
            )

    return trace


def _coerce_final_answer(value: Any) -> GroundedAgentAnswer:
    if isinstance(value, GroundedAgentAnswer):
        return value
    if isinstance(value, BaseModel):
        return GroundedAgentAnswer.model_validate(value.model_dump())
    if isinstance(value, Mapping):
        return GroundedAgentAnswer.model_validate(value)
    if isinstance(value, str):
        return GroundedAgentAnswer.model_validate_json(value)
    raise TypeError(f"Unsupported final output type: {type(value).__name__}")


def _retrieved_policy_chunks(trace: list[ToolTraceEvent]) -> dict[str, dict[str, Any]]:
    chunks: dict[str, dict[str, Any]] = {}
    for event in trace:
        if event.event_type != "tool_output" or event.tool_name != "search_policy":
            continue
        output = event.output
        if not isinstance(output, Mapping) or output.get("ok") is not True:
            continue
        data = output.get("data")
        if not isinstance(data, Mapping):
            continue
        results = data.get("results", [])
        if not isinstance(results, list):
            continue
        for item in results:
            if isinstance(item, Mapping) and item.get("chunk_id"):
                chunks[str(item["chunk_id"])] = dict(item)
    return chunks


def resolve_policy_sources(
    answer: GroundedAgentAnswer, trace: list[ToolTraceEvent]
) -> list[PolicySourceCitation]:
    retrieved = _retrieved_policy_chunks(trace)
    seen: set[str] = set()
    citations: list[PolicySourceCitation] = []
    for evidence in answer.evidence:
        for chunk_id in evidence.policy_chunk_ids:
            if chunk_id in seen or chunk_id not in retrieved:
                continue
            seen.add(chunk_id)
            item = retrieved[chunk_id]
            citations.append(
                PolicySourceCitation(
                    chunk_id=chunk_id,
                    source_title=str(item.get("source_title", "")),
                    source_url=str(item.get("source_url", "")),
                    section=None if item.get("section") is None else str(item.get("section")),
                    authority_level=None if item.get("authority_level") is None else str(item.get("authority_level")),
                )
            )
    return citations


def validate_grounded_answer(
    answer: GroundedAgentAnswer,
    used_tools: list[str],
    *,
    trace: list[ToolTraceEvent] | None = None,
    require_tool: bool = True,
) -> None:
    """Reject final outputs whose evidence does not match the actual tool trace."""
    if require_tool and not used_tools:
        raise AgentGroundingError(
            "The agent produced a final answer without calling a deterministic tool. "
            "This run is rejected as ungrounded."
        )
    if require_tool and not answer.evidence:
        raise AgentGroundingError(
            "The agent used deterministic tools but returned no evidence references. "
            "This run is rejected as insufficiently grounded."
        )

    used = set(used_tools)
    invalid_sources = sorted({item.source_tool for item in answer.evidence if item.source_tool not in used})
    if invalid_sources:
        raise AgentGroundingError(
            "The final answer cites tool evidence that does not exist in the run trace: "
            + ", ".join(invalid_sources)
        )

    policy_evidence = [item for item in answer.evidence if item.source_tool == "search_policy"]
    if policy_evidence:
        if "search_policy" not in used:
            raise AgentGroundingError("Policy evidence was supplied without a search_policy tool call.")
        if trace is None:
            raise AgentGroundingError("Policy grounding validation requires the tool trace.")
        retrieved_ids = set(_retrieved_policy_chunks(trace))
        for item in policy_evidence:
            if not item.policy_chunk_ids:
                raise AgentGroundingError(
                    "search_policy evidence must include at least one retrieved policy_chunk_id."
                )
            invalid_ids = sorted(set(item.policy_chunk_ids) - retrieved_ids)
            if invalid_ids:
                raise AgentGroundingError(
                    "The final answer cites policy chunks that were not retrieved in this run: "
                    + ", ".join(invalid_ids)
                )

    for item in answer.evidence:
        if item.source_tool != "search_policy" and item.policy_chunk_ids:
            raise AgentGroundingError(
                f"Non-policy evidence from {item.source_tool} must not contain policy_chunk_ids."
            )


def build_agent(model: str | None = None):
    """Construct the single ACECQA agent with analytics plus policy retrieval tools."""
    try:
        from agents import Agent
    except ImportError as exc:  # pragma: no cover - depends on optional runtime package
        raise RuntimeError(
            "OpenAI Agents SDK is not installed. Run: pip install -e '.[agent]'"
        ) from exc

    selected_model = model or os.getenv("ACECQA_AGENT_MODEL", DEFAULT_MODEL)
    return Agent(
        name="ACECQA Service Risk Copilot",
        instructions=SYSTEM_PROMPT,
        model=selected_model,
        model_settings={
            "reasoning": {"effort": "low"},
            "verbosity": "low",
            "parallel_tool_calls": False,
        },
        tools=build_openai_tools(),
        output_type=GroundedAgentAnswer,
    )


def run_copilot(
    query: str,
    *,
    model: str | None = None,
    require_tool: bool = True,
    max_turns: int = 8,
) -> AgentRunReport:
    """Run one user query through the single-agent loop and return an auditable report."""
    if not query.strip():
        raise ValueError("query must not be empty")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set.")

    try:
        from agents import Runner
    except ImportError as exc:  # pragma: no cover - depends on optional runtime package
        raise RuntimeError(
            "OpenAI Agents SDK is not installed. Run: pip install -e '.[agent]'"
        ) from exc

    selected_model = model or os.getenv("ACECQA_AGENT_MODEL", DEFAULT_MODEL)
    agent = build_agent(selected_model)
    started = time.perf_counter()
    result = Runner.run_sync(agent, query, max_turns=max_turns)
    latency_ms = (time.perf_counter() - started) * 1000
    trace = extract_tool_trace(result.new_items)
    used_tools = []
    for event in trace:
        if event.event_type == "tool_call" and event.tool_name and event.tool_name not in used_tools:
            used_tools.append(event.tool_name)

    final_answer = _coerce_final_answer(result.final_output)
    sdk_usage = result.context_wrapper.usage
    report = AgentRunReport(
        query=query,
        model=selected_model,
        answer=final_answer,
        used_tools=used_tools,
        tool_trace=trace,
        policy_sources=resolve_policy_sources(final_answer, trace),
        usage=AgentUsageSummary(
            requests=getattr(sdk_usage, "requests", 0),
            input_tokens=getattr(sdk_usage, "input_tokens", 0),
            output_tokens=getattr(sdk_usage, "output_tokens", 0),
            total_tokens=getattr(sdk_usage, "total_tokens", 0),
        ),
        latency_ms=latency_ms,
    )
    try:
        validate_grounded_answer(final_answer, used_tools, trace=trace, require_tool=require_tool)
    except AgentGroundingError as exc:
        exc.report = report
        raise
    return report
