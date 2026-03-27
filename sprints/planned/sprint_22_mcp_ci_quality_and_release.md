# Sprint 22: Cross-Repo Quality Gates and Final Release Checklist

## Goal

Close out the cross-repo integration with explicit quality gates for PyPack and optional Midterm_Ordo chat integration.

## Scope

- Validate Phase 1 (PyPack MCP server) definition of done.
- Validate Phase 2 (Midterm_Ordo optional chat integration) definition of done.
- Ensure env vars and runtime setup docs are complete in both repos.
- Produce final handoff checklist with residual risks.

## Hard Gates for Optional Sprints

- Sprint 20 required when Midterm runtime must invoke MCP subprocess in this release.
- Sprint 20 skipped only for PyPack-only release where Midterm integration is explicitly out of scope.
- Sprint 21 required when chat ToolRegistry exposure is in scope.
- Sprint 21 skipped when MCP integration is backend-only without chat descriptor registration.

## Quality Gates

### PyPack_GarysGuide

- `poetry run pytest`
- `poetry run mypy src tests`
- `poetry run ruff check .`
- `poetry run ruff format --check .`

### Midterm_Ordo (if enabled)

- `npm run test`
- `npm run typecheck`
- `npm run lint:strict`
- optional: `npm run test:integration`
- tool-count expectation tests updated after registration
- role visibility expectation tests updated for allowed/disallowed roles
- alias mapping tests when dot-name fallback is active

## Observability Minimums

- subprocess start/stop/crash events are logged and queryable
- tool invocation success/failure counts are emitted
- normalized error code frequency is emitted and reviewable

## Definition of Done

### PyPack MCP Server

1. `poetry run python -m garys_nyc_events.mcp.server` starts.
2. `ListTools` returns exactly `garys_events.query_events`.
3. `CallTool` succeeds on valid payload.
4. Errors are normalized and safe.
5. pytest/mypy/ruff all pass.

### Midterm_Ordo (Optional)

1. Subprocess start/cleanup is reliable.
2. Descriptor is registered and validated.
3. Allowed roles can use tool; disallowed roles are blocked.
4. Chat call executes tool via subprocess successfully.
5. Tool-count and role visibility test updates pass.
6. test/typecheck/lint:strict pass.

## Tasks

1. Add/update CI jobs and quality scripts in both repos.
2. Finalize env var docs for both repositories.
3. Add release runbook steps for local and production startup.
4. Capture residual risks and owner assignments.

## Exit Criteria

- All relevant quality gates are green.
- Both repo checklists are complete.
- Integration is ready for merge with no blocker.
- No merge in either repo until the cross-repo integration matrix passes in the same release-candidate window.
