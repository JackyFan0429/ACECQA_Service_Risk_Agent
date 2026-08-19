"""OpenAI Agents SDK FunctionTool wrappers for the deterministic analytics layer."""

from __future__ import annotations

from typing import Any

from acecqa_agent.agent.tool_adapter import TOOL_SPECS, invoke_registered_tool_json


def build_openai_tools() -> list[Any]:
    """Build FunctionTool objects lazily so the core package remains testable offline."""
    try:
        from agents import FunctionTool
    except ImportError as exc:  # pragma: no cover - depends on optional runtime package
        raise RuntimeError(
            "OpenAI Agents SDK is not installed. Run: pip install -e '.[agent]'"
        ) from exc

    tools: list[Any] = []
    for spec in TOOL_SPECS.values():
        tool_name = spec.name

        async def on_invoke_tool(ctx: Any, args_json: str, *, _tool_name: str = tool_name) -> str:
            del ctx
            return invoke_registered_tool_json(_tool_name, args_json)

        tools.append(
            FunctionTool(
                name=spec.name,
                description=spec.description,
                params_json_schema=spec.input_model.model_json_schema(),
                on_invoke_tool=on_invoke_tool,
                strict_json_schema=True,
                timeout_seconds=30.0,
                timeout_behavior="error_as_result",
            )
        )
    return tools
