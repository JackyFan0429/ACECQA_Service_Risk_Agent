"""Framework-neutral deterministic tool registry for the Single Agent.

The same business tools can later be exposed through another runtime or MCP without
rewriting the analytics/scenario logic.
"""

from acecqa_agent.tools import (
    analyse_transport_quartile_outcomes,
    calculate_risk_score,
    compare_transport_access,
    find_high_risk_services,
    get_service_profile,
    search_policy,
    simulate_risk_thresholds,
    compare_risk_scenarios,
    search_services,
)

TOOL_REGISTRY = {
    "search_services": search_services,
    "get_service_profile": get_service_profile,
    "calculate_risk_score": calculate_risk_score,
    "find_high_risk_services": find_high_risk_services,
    "compare_transport_access": compare_transport_access,
    "analyse_transport_quartile_outcomes": analyse_transport_quartile_outcomes,
    "search_policy": search_policy,
    "simulate_risk_thresholds": simulate_risk_thresholds,
    "compare_risk_scenarios": compare_risk_scenarios,
}
