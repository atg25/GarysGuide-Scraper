# Midterm_Ordo Handoff Package (Sprints 20/21)

## Purpose

This package transfers Sprint 20/21 implementation responsibilities to the Midterm_Ordo team while Sprint 20 remains active and blocked-external in PyPack.

## Dependency Context

- Upstream provider: PyPack MCP server already available via `python -m garys_nyc_events.mcp.server`.
- Consumer/runtime owner: Midterm_Ordo.
- Canonical MCP tool name: `garys_events.query_events`.

## 1. Required Code Changes

### A. Subprocess Lifecycle Integration (Sprint 20)

Implement a bootstrap module in Midterm_Ordo responsible for:

1. Starting subprocess:

- command: `poetry run python -m garys_nyc_events.mcp.server`
- cwd: `process.env.GARYS_EVENTS_MCP_REPO_PATH || "../PyPack_GarysGuide"`

2. Runtime resilience policy:

- startup timeout (recommended default: 10s)
- crash detection and structured error logging
- retry/backoff on startup failures (bounded attempts)
- clean shutdown on app termination signals

3. Runtime mode toggle:

- default mode: fail-open
- optional mode: fail-closed (operator toggle)

4. Fail-open behavior (default):

- chat remains available
- MCP tool is hidden/disabled when subprocess unavailable

5. Fail-closed behavior (toggle):

- MCP tool operations are rejected until subprocess healthy

### B. Chat Descriptor Integration (Sprint 21)

1. Add descriptor file:

- `src/core/use-cases/tools/garys-events-query.tool.ts`

2. Dot-name compatibility decision before registration:

- run compatibility check before calling registry registration
- do not register and then rename (avoid registration churn)

3. Deterministic alias behavior:

- canonical MCP name: `garys_events.query_events`
- chat alias (fallback only): `garys_events_query_events`
- deterministic mapping: `garys_events_query_events -> garys_events.query_events`
- one-to-one mapping helper; no alternate targets permitted

4. Register descriptor in:

- `src/lib/chat/tool-composition-root.ts`

## 2. Required Tests

### Sprint 20 Tests (Subprocess lifecycle)

Unit:

- subprocess command/cwd construction
- missing env fast-fail path
- startup timeout path

Integration:

- startup success path
- crash handling path
- retry/backoff stops at cap
- shutdown cleanup path
- default fail-open policy path
- fail-closed toggle path

E2E:

- chat/tool invocation works when subprocess healthy
- subprocess crash returns normalized safe error to chat layer

### Sprint 21 Tests (Descriptor/roles/alias)

Unit:

- descriptor schema valid
- role visibility allow/block behavior
- alias helper maps only to canonical MCP tool

Integration:

- tool-count expectation updated after registration
- role visibility matrix updated for allowed/disallowed roles
- unauthorized role blocked on execution

E2E:

- allowed role can invoke tool through subprocess
- blocked role denied with safe response

## 3. Required Env Wiring (Midterm-owned injection)

Midterm must inject these env vars into subprocess runtime:

- `GARYS_EVENTS_REST_API_BASE_URL`
- `GARYS_EVENTS_REST_API_TIMEOUT_MS` (default `10000`)
- `GARYS_EVENTS_MCP_REPO_PATH` (default `../PyPack_GarysGuide`)
- `GARYS_EVENTS_MCP_ENABLED` (default `true`)

Ownership rule:

- Midterm is source of env injection.
- PyPack consumes env only.

## 4. Acceptance Checklist Mapped to Sprint Exit Criteria

### Sprint 20 Exit Criteria Mapping

- [ ] Midterm launches/manages PyPack MCP subprocess reliably
- [ ] Lifecycle tests cover start/timeout/crash/retry/stop
- [ ] Fail-open/fail-closed behavior deterministic and tested

### Sprint 21 Exit Criteria Mapping

- [ ] Dot-name compatibility checked before registration
- [ ] Alias fallback deterministic and one-to-one
- [ ] Tool-count tests updated and passing
- [ ] Role visibility/blocking tests updated and passing
- [ ] Allowed role executes; blocked role denied

## Delivery Back to PyPack Team

Provide these artifacts for closure:

1. PR link(s) with changed files list
2. test output for `npm run test`
3. typecheck output for `npm run typecheck`
4. lint output for `npm run lint:strict`
5. evidence for fail-open default and fail-closed toggle
6. evidence for alias decision timing and deterministic mapping behavior
