from __future__ import annotations

import json
import os
import sys
from typing import Any, Callable, Mapping, TextIO

from .tools import query_events


TOOL_NAME = "garys_events.query_events"
Handler = Callable[[Mapping[str, Any]], dict[str, Any]]


def _enabled_from_env() -> bool:
    value = os.getenv("GARYS_EVENTS_MCP_ENABLED", "true").strip().lower()
    return value not in {"0", "false", "no", "off"}


def _error(code: str, message: str, retriable: bool = False) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {"code": code, "message": message, "retriable": retriable},
    }


def list_tools(*, enabled: bool | None = None) -> list[dict[str, Any]]:
    if enabled is None:
        enabled = _enabled_from_env()
    if not enabled:
        return []
    return [
        {
            "name": TOOL_NAME,
            "description": "Query NYC events from Gary's Guide",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "ai_only": {"type": "boolean", "default": True},
                    "limit": {"type": "integer", "minimum": 0, "maximum": 500},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "date_from": {
                        "type": "string",
                        "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
                    },
                    "date_to": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                },
                "additionalProperties": False,
            },
        }
    ]


def call_tool(
    name: str,
    arguments: Mapping[str, Any] | None = None,
    *,
    handler: Handler = query_events,
    enabled: bool | None = None,
) -> dict[str, Any]:
    if enabled is None:
        enabled = _enabled_from_env()
    if not enabled:
        return _error("tool_disabled", "MCP tool is disabled")
    if name != TOOL_NAME:
        return _error("unknown_tool", "Unknown tool name")

    safe_args: Mapping[str, Any] = arguments or {}
    try:
        result = handler(safe_args)
        if not isinstance(result, dict):
            raise TypeError("handler must return dict")
        json.dumps(result)
        return result
    except Exception:
        return _error("tool_execution_failed", "Tool execution failed")


def _handle_request(
    request: dict[str, Any],
    *,
    handler: Handler,
    enabled: bool | None,
) -> dict[str, Any]:
    method = str(request.get("method", ""))
    params = request.get("params", {})

    if method == "ListTools":
        return {"tools": list_tools(enabled=enabled)}

    if method == "CallTool":
        if not isinstance(params, Mapping):
            return _error("invalid_request", "params must be an object")
        name = str(params.get("name", ""))
        arguments = params.get("arguments", {})
        if not isinstance(arguments, Mapping):
            return _error("invalid_request", "arguments must be an object")
        return call_tool(name, arguments, handler=handler, enabled=enabled)

    return _error("method_not_supported", "Unsupported method")


def run_stdio_loop(
    *,
    in_stream: TextIO = sys.stdin,
    out_stream: TextIO = sys.stdout,
    handler: Handler = query_events,
    enabled: bool | None = None,
) -> None:
    while True:
        raw = in_stream.readline()
        if raw == "":
            break

        line = raw.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            if not isinstance(request, dict):
                raise ValueError("request must be object")
            response = _handle_request(request, handler=handler, enabled=enabled)
        except Exception:
            response = _error("invalid_json", "Invalid request JSON")

        out_stream.write(json.dumps(response) + "\n")
        out_stream.flush()


def main() -> None:
    run_stdio_loop()


if __name__ == "__main__":
    main()
