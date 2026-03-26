#!/usr/bin/env bash
set -euo pipefail

# Fast MCP smoke checks for pre-staging readiness.
# These checks validate contract shape and deterministic behavior without external services.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -x ".test-venv/bin/python" ]]; then
  PYTHON_BIN=".test-venv/bin/python"
else
  PYTHON_BIN="python3"
fi

PYTHONPATH="$ROOT_DIR/src" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import sys

from garys_nyc_events.mcp.server import TOOL_NAME, call_tool, list_tools


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def assert_error_shape(payload: dict) -> None:
    if payload.get("ok") is not False:
        fail("error payload missing ok=false")
    err = payload.get("error")
    if not isinstance(err, dict):
        fail("error payload missing error object")
    for key in ("code", "message", "retriable"):
        if key not in err:
            fail(f"error payload missing error.{key}")


print("[1/4] ListTools canonical registration")
tools = list_tools(enabled=True)
if len(tools) != 1:
    fail(f"expected exactly 1 tool, got {len(tools)}")
if tools[0].get("name") != TOOL_NAME:
    fail("canonical tool name mismatch")
print("OK: ListTools returns only canonical tool")

print("[2/4] CallTool success envelope")

def success_handler(_args: dict) -> dict:
    return {"ok": True, "data": {"count": 1, "events": [{"id": "evt_1"}]}}

success = call_tool(TOOL_NAME, {"limit": 1}, handler=success_handler, enabled=True)
if success.get("ok") is not True:
    fail("success call did not return ok=true")
data = success.get("data")
if not isinstance(data, dict) or "count" not in data or "events" not in data:
    fail("success payload missing data.count or data.events")
print("OK: CallTool success shape is valid")

print("[3/4] CallTool validation error envelope")
validation_err = call_tool(TOOL_NAME, {"limit": 999}, enabled=True)
assert_error_shape(validation_err)
if validation_err["error"]["code"] != "validation_error":
    fail("expected validation_error for invalid limit")
print("OK: validation error shape and code are valid")

print("[4/4] CallTool unknown tool envelope")
unknown_tool = call_tool("not.real.tool", {"limit": 1}, enabled=True)
assert_error_shape(unknown_tool)
if unknown_tool["error"]["code"] != "unknown_tool":
    fail("expected unknown_tool for unknown tool call")
print("OK: unknown tool error shape and code are valid")

print("\nPASS: MCP smoke checks completed")
print(json.dumps({"tool": TOOL_NAME, "checks": 4, "result": "pass"}))
PY
