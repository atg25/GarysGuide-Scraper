# MCP Tool Integration Plan (PM Letter Aligned)

**Two-repository model, stdio subprocess transport**

## Architecture Overview

This integration spans two repositories with one stable tool identity:

1. PyPack_GarysGuide (Python)

- Adds an MCP server as a pure addition.
- Wraps existing REST API behavior without changing it.
- Exposes exactly one tool: `garys_events.query_events`.
- Runs over stdio as a subprocess.

2. Midterm_Ordo (TypeScript/Next.js)

- Starts the PyPack MCP server as a child process.
- Optionally registers a chat descriptor in ToolRegistry.
- Calls the tool through existing chat middleware and registry flow.

## Transport and Runtime Model

- Transport: stdio subprocess.
- Standard server process command (PyPack): `poetry run python -m garys_nyc_events.mcp.server`.
- Midterm_Ordo starts process using `spawn(...)` and manages lifecycle.
- Existing REST API remains unchanged.

## Naming Compatibility Rule (Anthropic/Chat)

- Canonical MCP tool name remains `garys_events.query_events`.
- Midterm must validate whether chat tool names allow dots.
- If dot names are unsupported, use chat alias `garys_events_query_events`.
- Alias mapping must be deterministic and one-to-one:
  - Chat name `garys_events_query_events` -> MCP call `garys_events.query_events`
  - Reverse mapping only for logs/observability (never for auth decisions)
- Dot-name compatibility check must run before descriptor registration to avoid registration churn.

## Tool Contract (Frozen)

Name: `garys_events.query_events`

Input:

- `ai_only`: boolean (default `true`)
- `limit`: integer `0..500`
- `tags`: optional array of lowercase strings
- `date_from`: optional `YYYY-MM-DD`
- `date_to`: optional `YYYY-MM-DD`

Success output:

- `ok: true`
- `data.count`: integer
- `data.events`: array of normalized event objects

Failure output:

- `ok: false`
- `error.code`: stable machine code
- `error.message`: safe user-facing message
- `error.retriable`: boolean

## Environment Variables

Ownership rule:

- Midterm_Ordo is the source of env injection for subprocess runtime.
- PyPack MCP server only consumes env vars; it does not infer or mutate Midterm env.

PyPack_GarysGuide:

- `GARYS_EVENTS_REST_API_BASE_URL`
- `GARYS_EVENTS_REST_API_TIMEOUT_MS` (default `10000`)
- `GARYS_EVENTS_MCP_ENABLED` (default `true`)

Midterm_Ordo:

- `GARYS_EVENTS_REST_API_BASE_URL`
- `GARYS_EVENTS_REST_API_TIMEOUT_MS` (default `10000`)
- `GARYS_EVENTS_MCP_REPO_PATH` (default `../PyPack_GarysGuide`)
- `GARYS_EVENTS_MCP_ENABLED` (default `true`)

## File Targets

PyPack_GarysGuide:

- `src/garys_nyc_events/mcp/__init__.py`
- `src/garys_nyc_events/mcp/server.py`
- `src/garys_nyc_events/mcp/tools/__init__.py`
- `src/garys_nyc_events/mcp/tools/query_events.py`
- `tests/test_mcp_server_unit.py`
- `tests/test_mcp_contract_integration.py`
- `tests/test_mcp_e2e.py`
- `pyproject.toml` (MCP dependency + runnable module support)

Midterm_Ordo (optional chat integration):

- `src/core/use-cases/tools/garys-events-query.tool.ts`
- `src/lib/chat/tool-composition-root.ts`
- integration/unit tests for descriptor + subprocess behavior
- alias mapping helper (only if dot-name validation fails)

## Sprint Plan (Updated)

### Sprint 16 (PyPack): Foundation and Contract Freeze

- Freeze contract fixtures for input/success/failure.
- Add baseline regression tests to ensure REST behavior unchanged.
- Lock env vars and defaults.
- Exit: contract and baseline tests approved.

### Sprint 17 (PyPack): MCP Server Runtime and Stdio Dispatch

- Add pinned `modelcontextprotocol==1.0.0` dependency.
- Implement stdio server entrypoint in `src/garys_nyc_events/mcp/server.py`.
- Register one tool and deterministic dispatch.
- Gate with `GARYS_EVENTS_MCP_ENABLED`.
- Exit: server starts, `ListTools` returns one tool, `CallTool` deterministic.

### Sprint 18 (PyPack): REST Adapter and Error Normalization

- Implement REST call path inside `query_events` tool.
- Use base URL + timeout env vars.
- Normalize all failures into stable envelope.
- Ensure no internal/secret leakage in errors.
- Enforce stable retriable taxonomy:
  - retriable: timeout, HTTP 429, HTTP 503, HTTP 504, network disconnect/reset
  - non-retriable: all other 4xx validation/auth/client errors
- Exit: success/failure contract snapshots pass.

### Sprint 19 (PyPack): Validation, Security Assertions, Quality Gates

- Enforce strict schema and bounds (`additionalProperties: false`, `limit 0..500`, dates).
- Add negative tests for malformed payloads and leakage prevention.
- Pass required quality commands.
- Exit: Phase 1 DoD complete and MCP server ready for Midterm_Ordo.

### Sprint 20 (Midterm_Ordo, optional): Subprocess Lifecycle Integration

- Start PyPack MCP process with `spawn("poetry", ["run", "python", "-m", "garys_nyc_events.mcp.server"])`.
- Configure cwd from `GARYS_EVENTS_MCP_REPO_PATH`.
- Add startup timeout, crash handling, retry/backoff, and shutdown cleanup.
- Define explicit fail-open/fail-closed runtime behavior.
- Default runtime policy is fail-open for app availability.
- Operator toggle enables fail-closed mode for high-assurance environments.
- Exit: reliable process lifecycle in app runtime.

### Sprint 21 (Midterm_Ordo, optional): Chat Descriptor and Role Controls

- Add descriptor `createGarysEventsQueryTool()`.
- Register in tool composition root.
- Validate dot-name compatibility; if unsupported, register alias `garys_events_query_events` with deterministic mapping to MCP canonical name.
- Enforce least-privilege role visibility/blocking.
- Exit: allowed roles can use tool, disallowed roles cannot.

### Sprint 22 (Cross-repo): Final Quality and Release Checklist

- Run all relevant quality gates in both repos.
- Verify deployment/runtime docs and env setup.
- Complete final DoD and residual risk check.
- Exit: integration merge-ready.

## Quality Checklists

PyPack_GarysGuide:

- `poetry run pytest`
- `poetry run mypy src tests`
- `poetry run ruff check .`
- `poetry run ruff format --check .`

Midterm_Ordo (if enabled):

- `npm run test`
- `npm run typecheck`
- `npm run lint:strict`
- optional: `npm run test:integration`

Midterm test additions (required when Sprint 21 enabled):

- tool-count expectations updated after registration
- role visibility expectations for allowed and disallowed roles
- alias mapping tests when dot-name fallback is active

Observability minimums (required):

- subprocess start/stop/crash events
- tool invocation success/failure counts
- normalized error code frequency

## Definition of Done

PyPack MCP server:

1. Server starts with `poetry run python -m garys_nyc_events.mcp.server`.
2. `ListTools` returns exactly `garys_events.query_events`.
3. `CallTool` executes successfully with valid payload.
4. Errors are normalized and safe.
5. pytest, mypy, and ruff checks pass.

Midterm_Ordo integration (optional):

1. Subprocess starts and stops cleanly.
2. Descriptor is registered and validates.
3. Allowed roles can use tool; disallowed roles are blocked.
4. Chat invokes tool via subprocess successfully.
5. Tool-count and role visibility tests are updated and pass.
6. test/typecheck/lint:strict pass.

## Security Requirements

PyPack:

- Never leak secrets in tool errors.
- Never expose stack traces/internal network details in tool output.
- Validation is mandatory before execution.

Midterm_Ordo:

- Subprocess hygiene: startup timeout, retry/backoff, crash handling, shutdown cleanup required.
- Role checks from execution context/middleware, never from LLM input.
- Runtime policy must be explicit:
  - fail-open (default): chat remains available and MCP tool is hidden/disabled when subprocess is unavailable
  - fail-closed (operator-enabled): chat tool layer rejects tool operations until MCP subprocess is healthy

## Deployment Notes

Local development:

PyPack:

1. Start REST API: `poetry run python -m garys_nyc_events.api`
2. Start MCP: `GARYS_EVENTS_REST_API_BASE_URL=http://localhost:8000 poetry run python -m garys_nyc_events.mcp.server`

Midterm_Ordo:

1. Set `GARYS_EVENTS_REST_API_BASE_URL=http://localhost:8000`
2. Set `GARYS_EVENTS_MCP_REPO_PATH=../PyPack_GarysGuide`
3. Start app (`npm run dev`) and let it spawn MCP subprocess.

Production:

- Keep repos deployed independently.
- Preserve stdio transport model only when Midterm and PyPack are locally co-located.
- If independent remote deployment is required, replace stdio subprocess with network transport.
- Configure env vars explicitly per environment.

## Optional Sprint Hard Gates

- Sprint 20 is required if Midterm must invoke MCP from app runtime (subprocess path in scope).
- Sprint 20 is skipped only when delivery is PyPack-only and Midterm integration is explicitly out of scope for the release.
- Sprint 21 is required only when chat ToolRegistry exposure is in scope.
- Sprint 21 is skipped when MCP is integrated without chat descriptor exposure.

## Cross-Repo Release Gate

- No merge in either repository until the cross-repo integration matrix passes in the same release-candidate window.

## Traceability Matrix

| PM Requirement                                     | Where Covered                         |
| -------------------------------------------------- | ------------------------------------- |
| One stable tool name                               | Contract section + Sprint 16          |
| Dot-name compatibility and alias mapping           | Naming compatibility rule + Sprint 21 |
| Stdio subprocess model                             | Runtime model + Sprint 17 + Sprint 20 |
| Co-location constraint / remote transport fallback | Deployment notes                      |
| PyPack server wraps REST API                       | Sprints 17-19                         |
| Strict validation and safe errors                  | Sprints 18-19                         |
| Midterm optional chat integration                  | Sprints 20-21                         |
| Role-based visibility                              | Sprint 21                             |
| Midterm tool-count + role visibility test updates  | Quality checklists + Sprint 21/22     |
| Env ownership (Midterm injects, PyPack consumes)   | Environment variables section         |
| Default runtime policy + operator toggle           | Sprint 20 + Security requirements     |
| Explicit retriable error taxonomy                  | Sprint 18                             |
| Observability minimums                             | Quality checklists                    |
| Cross-repo merge gate                              | Cross-repo release gate               |
| Quality gates (PyPack + Midterm)                   | Sprint 22 + Quality Checklists        |
| Final cross-repo DoD                               | Definition of Done + Sprint 22        |
