from types import SimpleNamespace

from acecqa_agent.agent.runtime import extract_tool_trace


class ToolCallItem:
    def __init__(self):
        self.raw_item = SimpleNamespace(
            name="find_high_risk_services",
            call_id="call_1",
            arguments='{"state":"QLD","urban_rural":"Rural"}',
        )


class ToolCallOutputItem:
    def __init__(self):
        self.raw_item = SimpleNamespace(call_id="call_1")
        self.output = '{"ok":true,"tool":"find_high_risk_services","data":{"matched_count":21}}'


def test_extract_tool_trace_links_call_and_output():
    trace = extract_tool_trace([ToolCallItem(), ToolCallOutputItem()])
    assert len(trace) == 2
    assert trace[0].tool_name == "find_high_risk_services"
    assert trace[0].arguments["state"] == "QLD"
    assert trace[1].tool_name == "find_high_risk_services"
    assert trace[1].output["data"]["matched_count"] == 21

from acecqa_agent.agent.runtime import (
    AgentGroundingError,
    GroundedAgentAnswer,
    GroundedEvidence,
    validate_grounded_answer,
)


def test_grounding_validation_rejects_evidence_for_tool_not_called():
    answer = GroundedAgentAnswer(
        answer="Example",
        evidence=[GroundedEvidence(source_tool="search_services", claim="Example claim")],
    )
    try:
        validate_grounded_answer(answer, ["find_high_risk_services"])
    except AgentGroundingError as exc:
        assert "does not exist" in str(exc)
    else:
        raise AssertionError("Expected AgentGroundingError")


def test_grounding_validation_accepts_matching_tool_evidence():
    answer = GroundedAgentAnswer(
        answer="Example",
        evidence=[
            GroundedEvidence(
                source_tool="find_high_risk_services",
                claim="21 triple-gap QLD rural CBC services",
            )
        ],
    )
    validate_grounded_answer(answer, ["find_high_risk_services"])


def test_policy_grounding_rejects_unretrieved_chunk_id():
    from acecqa_agent.agent.runtime import ToolTraceEvent

    answer = GroundedAgentAnswer(
        answer="Example",
        evidence=[
            GroundedEvidence(
                source_tool="search_policy",
                claim="Policy claim",
                policy_chunk_ids=["POL-fake-9999"],
            )
        ],
    )
    trace = [
        ToolTraceEvent(
            sequence=1,
            event_type="tool_output",
            tool_name="search_policy",
            call_id="call_p1",
            output={
                "ok": True,
                "tool": "search_policy",
                "data": {"results": [{"chunk_id": "POL-real-0001"}]},
            },
        )
    ]
    try:
        validate_grounded_answer(answer, ["search_policy"], trace=trace)
    except AgentGroundingError as exc:
        assert "were not retrieved" in str(exc)
    else:
        raise AssertionError("Expected AgentGroundingError")


def test_policy_grounding_accepts_retrieved_chunk_and_resolves_source():
    from acecqa_agent.agent.runtime import ToolTraceEvent, resolve_policy_sources

    answer = GroundedAgentAnswer(
        answer="Example",
        evidence=[
            GroundedEvidence(
                source_tool="search_policy",
                claim="Policy claim",
                policy_chunk_ids=["POL-real-0001"],
            )
        ],
    )
    trace = [
        ToolTraceEvent(
            sequence=1,
            event_type="tool_output",
            tool_name="search_policy",
            call_id="call_p1",
            output={
                "ok": True,
                "tool": "search_policy",
                "data": {
                    "results": [
                        {
                            "chunk_id": "POL-real-0001",
                            "source_title": "Official source",
                            "source_url": "https://www.acecqa.gov.au/example",
                            "section": "Example section",
                            "authority_level": "official_guidance",
                        }
                    ]
                },
            },
        )
    ]
    validate_grounded_answer(answer, ["search_policy"], trace=trace)
    sources = resolve_policy_sources(answer, trace)
    assert len(sources) == 1
    assert sources[0].source_url == "https://www.acecqa.gov.au/example"
