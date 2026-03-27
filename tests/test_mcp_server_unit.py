from __future__ import annotations

from typing import Any, Mapping

from garys_nyc_events.mcp.server import TOOL_NAME, call_tool, list_tools


def test_list_tools_returns_exact_single_tool_when_enabled():
    tools = list_tools(enabled=True)

    assert len(tools) == 1
    assert tools[0]["name"] == TOOL_NAME


def test_list_tools_returns_empty_when_disabled():
    assert list_tools(enabled=False) == []


def test_call_tool_routes_to_handler_for_exact_name():
    seen: dict[str, Any] = {}

    def _handler(arguments: Mapping[str, Any]) -> dict[str, Any]:
        seen["arguments"] = dict(arguments)
        return {"ok": True, "data": {"count": 0, "events": []}}

    payload = {"limit": 10}
    result = call_tool(TOOL_NAME, payload, handler=_handler, enabled=True)

    assert result["ok"] is True
    assert seen["arguments"] == payload


def test_call_tool_unknown_name_is_normalized_error():
    result = call_tool("not.a.tool", {"limit": 1}, enabled=True)

    assert result["ok"] is False
    assert result["error"]["code"] == "unknown_tool"


def test_call_tool_disabled_is_normalized_error():
    result = call_tool(TOOL_NAME, {"limit": 1}, enabled=False)

    assert result["ok"] is False
    assert result["error"]["code"] == "tool_disabled"


def test_call_tool_handler_exception_is_sanitized():
    def _handler(_arguments: Mapping[str, Any]) -> dict[str, Any]:
        raise RuntimeError("boom internal detail")

    result = call_tool(TOOL_NAME, {"limit": 1}, handler=_handler, enabled=True)

    assert result["ok"] is False
    assert result["error"]["code"] == "tool_execution_failed"
    assert "boom" not in result["error"]["message"].lower()
