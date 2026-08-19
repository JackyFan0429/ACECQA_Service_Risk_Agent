import json
from pathlib import Path

from acecqa_agent.agent.tool_adapter import TOOL_SPECS

payload = {
    name: {
        "description": spec.description,
        "input_schema": spec.input_model.model_json_schema(),
        "output_schema": spec.output_model.model_json_schema(),
    }
    for name, spec in TOOL_SPECS.items()
}

out = Path(__file__).parent / "docs" / "tool_schemas.json"
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(out)
