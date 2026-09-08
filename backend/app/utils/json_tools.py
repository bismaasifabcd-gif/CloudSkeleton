from __future__ import annotations

import json
from typing import Any


class JsonExtractionError(ValueError):
    pass


def extract_json_object(text: str) -> dict[str, Any]:
    """Extract a JSON object from model output that may include prose fences."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = [line for line in stripped.splitlines() if not line.startswith("```")]
        stripped = "\n".join(lines).strip()

    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise JsonExtractionError("No JSON object was found in the model output")
        try:
            parsed = json.loads(stripped[start : end + 1])
        except json.JSONDecodeError as exc:
            raise JsonExtractionError(str(exc)) from exc

    if not isinstance(parsed, dict):
        raise JsonExtractionError("Expected a JSON object at the top level")
    return parsed
