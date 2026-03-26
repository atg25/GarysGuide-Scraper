# Sprint 17: MCP Server Runtime and Stdio Dispatch (PyPack)

## Goal

Implement Python MCP server runtime using `modelcontextprotocol` and expose deterministic `ListTools` and `CallTool` over stdio.

## Scope

- Add `mcp/` package and server entrypoint.
- Register exactly one tool: `garys_events.query_events`.
- Dispatch by exact tool name only.
- Respect `GARYS_EVENTS_MCP_ENABLED` for listing and calling.

## Planned File Structure

- `src/garys_nyc_events/mcp/__init__.py`
- `src/garys_nyc_events/mcp/server.py`
- `src/garys_nyc_events/mcp/tools/__init__.py`
- `src/garys_nyc_events/mcp/tools/query_events.py`
- `tests/test_mcp_server_unit.py`
- `tests/test_mcp_contract_integration.py`
- `tests/test_mcp_e2e.py`
- `pyproject.toml` (dependency + runnable entry)

## TDD Plan

### Unit

- Positive: `ListTools` returns exactly `garys_events.query_events` when enabled.
- Positive: `CallTool` dispatches to `query_events` by exact name.
- Negative: unknown tool returns normalized error.
- Negative: disabled server/tool is blocked.

### Integration

- Positive: MCP server process starts via stdio and responds to `ListTools`.
- Positive: valid `CallTool` payload reaches handler and returns JSON-safe dict.
- Negative: malformed request fails safely before handler.
- Negative: handler exception is normalized (no stack trace leakage).

### E2E

- Positive: `poetry run python -m garys_nyc_events.mcp.server` starts and responds.
- Positive: end-to-end `CallTool` succeeds with fixture payload.
- Negative: invalid tool name and invalid payload return deterministic errors.

## Tasks

1. Add pinned `modelcontextprotocol==1.0.0` dependency to `pyproject.toml`.
2. Implement `src/garys_nyc_events/mcp/server.py` stdio entrypoint.
3. Implement deterministic tool registry and dispatch.
4. Add MCP enabled gate.
5. Add first-pass normalized error wrapper.

## Exit Criteria

- Server starts with `poetry run python -m garys_nyc_events.mcp.server`.
- `ListTools` shows exactly one tool.
- `CallTool` is deterministic and tested.
- MCP SDK version is pinned exactly to `modelcontextprotocol==1.0.0` (no range specifier).
