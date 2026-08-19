"""Single-Agent MVP tool registry.

The LLM layer will be added on top of this registry. Keeping the registry framework-neutral
means the same deterministic tools can later be exposed via OpenAI Agents SDK, LangGraph,
or MCP without rewriting the analytics logic.
"""

from acecqa_agent.tools import (
    analyse_transport_quartile_outcomes,
    calculate_risk_score,
    compare_transport_access,
    find_high_risk_services,
    get_service_profile,
    search_services,
)

TOOL_REGISTRY = {
    "search_services": search_services,
    "get_service_profile": get_service_profile,
    "calculate_risk_score": calculate_risk_score,
    "find_high_risk_services": find_high_risk_services,
    "compare_transport_access": compare_transport_access,
    "analyse_transport_quartile_outcomes": analyse_transport_quartile_outcomes,
}
