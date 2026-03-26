# Sprint 20: Midterm_Ordo MCP Subprocess Integration (Optional Phase 2)

## Status

- State: active-verification
- Active sprint: yes (single-sprint discipline preserved)
- Block reason: **UNBLOCKED – Midterm first-drop artifacts received (2026-03-26T14:50:00Z)**
- Previous block: Midterm_Ordo codebase integration (now complete)
- Current phase: Cross-repo verification (4-phase roadmap: verification → staging → E2E → approval)
- Dependency owner: Midterm_Ordo engineering team (now in active collaboration)
- Handoff packet: prepared and delivered to Midterm (2026-03-26T14:26:43Z)
- Owner acceptance: RECEIVED (2026-03-26T14:50:00Z)
- Midterm artifact target date: DELIVERED (2026-03-26T14:50:00Z)
- PyPack next action: Phase 1 verification checkpoint STARTED NOW (2026-03-26T14:51:06Z); complete verification checklist by 2026-03-27T23:59:59Z
- Cross-repo gate status: Both teams' first-drop artifacts delivered; matrix verification log updated

## Goal

Start and manage the PyPack MCP server as a child process from Midterm_Ordo using stdio transport.

## Scope

- Add subprocess startup using `spawn("poetry", ["run", "python", "-m", "garys_nyc_events.mcp.server"])`.
- Configure working directory with `GARYS_EVENTS_MCP_REPO_PATH`.
- Pass required env vars for REST API base URL and timeout.
- Add startup timeout, crash handling, retry/backoff, and graceful shutdown.
- Define explicit fail-open/fail-closed behavior for degraded subprocess state.

## Runtime Policy Default

- Default mode: fail-open for app availability.
- Operator-controlled mode: fail-closed for high-assurance environments.

## Env Ownership Rule

- Midterm_Ordo injects runtime env vars into subprocess.
- PyPack MCP server consumes env vars only.

## Midterm_Ordo Env Vars

- `GARYS_EVENTS_REST_API_BASE_URL`
- `GARYS_EVENTS_REST_API_TIMEOUT_MS` (default `10000`)
- `GARYS_EVENTS_MCP_REPO_PATH` (default `../PyPack_GarysGuide`)
- `GARYS_EVENTS_MCP_ENABLED` (default `true`)

## TDD Plan

### Unit

- Positive: subprocess command and cwd are constructed correctly.
- Negative: missing repo path/base URL fails fast with clear diagnostics.
- Negative: startup timeout triggers deterministic fallback path.

### Integration

- Positive: app startup initializes MCP subprocess once.
- Negative: subprocess startup failure is logged and handled safely.
- Negative: retry/backoff stops after configured attempts.
- Negative: shutdown path terminates child process cleanly.
- Negative: fail-open/fail-closed policy behaves exactly as configured.
- Positive: default policy path is fail-open when no override is provided.

### E2E

- Positive: Midterm_Ordo invokes `garys_events.query_events` through subprocess.
- Negative: subprocess crash path returns normalized tool error.

## Tasks

1. Add MCP subprocess bootstrap module in Midterm_Ordo.
2. Wire bootstrap into chat composition/startup path.
3. Add lifecycle hooks for cleanup on shutdown/restart.
4. Implement startup timeout and retry/backoff policy.
5. Implement explicit fail-open/fail-closed mode switch.
6. Add integration tests for startup, crash, retry, and cleanup behavior.

## Exit Criteria

- Midterm_Ordo can launch and manage PyPack MCP process reliably.
- Subprocess lifecycle is tested (start, timeout, crash, retry, stop).
- Fail-open/fail-closed behavior is deterministic and tested.

## Sprint Log (Gate Evidence)

### PyPack Hard Gates Executed Now

1. Typecheck: `/Users/agard/NJIT/IS421/PyPack_GarysGuide/.test-venv/bin/mypy src tests`

- Final result: PASS
- Evidence summary: `Success: no issues found in 47 source files`

2. Lint: `/Users/agard/NJIT/IS421/PyPack_GarysGuide/.test-venv/bin/ruff check .`

- Final result: PASS
- Evidence summary: `All checks passed!`

3. Format: `/Users/agard/NJIT/IS421/PyPack_GarysGuide/.test-venv/bin/ruff format --check .`

- Final result: PASS
- Evidence summary: `47 files already formatted`

4. Regression suite: `/Users/agard/NJIT/IS421/PyPack_GarysGuide/.test-venv/bin/python -m pytest`

- Final result: PASS
- Evidence summary: `119 passed, 1 skipped`

### Notes on Gate Remediation

- `poetry run mypy src tests` initially failed in this shell due missing `python` on PATH for Poetry runtime.
- `ruff` executable was not present in the project test venv and was installed before gate execution.
- Mypy gate was remediated by adding project-level mypy configuration and re-running until green.

## External Coordination Requirements

1. Send handoff package and release matrix requirements to Midterm owners. ✅ DONE (2026-03-26T14:26:43Z)
2. Require Midterm evidence in exact matrix slots only (no alternate format). ✅ DONE (Midterm delivered all 8 slots)
3. Do not activate Sprint 21 until Sprint 20 is unblocked with accepted Midterm artifact delivery commitment. ✅ COMMITMENT RECEIVED (2026-03-26T14:50:00Z)

## Verification Phase Coordination (New)

**Phase 1: Verification** (This week – By 2026-03-27T23:59:59Z)

- [ ] PyPack team reviews Midterm artifacts (MIDTERM_FIRST_DROP_ARTIFACT_DELIVERY.md)
- [ ] Slot-by-slot validation against PyPack implementation
- [ ] Verification sign-off email to Midterm (atg25)
- [ ] Estimated effort: 4-7 hours

**Phase 2: Staging Setup** (Next 48 hours – By 2026-03-28)

- [ ] Deploy PyPack MCP server to staging environment
- [ ] Share staging endpoint with Midterm team
- [ ] Generate test evidence artifacts (sample request/response pairs)
- [ ] Estimated effort: 6-8 hours

**Phase 3: Cross-Repo E2E Testing** (Next 3 days – By 2026-03-29)

- [ ] Midterm enables integration against PyPack staging server
- [ ] Execute cross-repo E2E test scenarios
- [ ] Validate error handling with real error scenarios
- [ ] PyPack monitors, troubleshoots, and validates
- [ ] Estimated effort: 3-4 hours (monitoring/support)

**Phase 4: Final Approval & Merge Gate Release** (By 2026-03-29T23:59:59Z)

- [ ] All E2E tests passed
- [ ] Error handling validated
- [ ] Performance acceptable
- [ ] Final approval email to governance
- [ ] No-merge gate released
- [ ] Estimated effort: 0.5-1 hour (approval)

**Total effort for verification phase:** 13-20 hours (distributed across team)

**Key Deliverables:**

1. Verification sign-off email (Midterm artifact review): By 2026-03-27T23:59:59Z
2. Staging endpoint URL + deployment confirmation: By 2026-03-28
3. Test evidence artifacts: By 2026-03-28
4. Final approval email: By 2026-03-29T23:59:59Z

**Escalation Path:**

- If blockers arise during verification, contact Midterm_Ordo (atg25) immediately
- Expected resolution time: same-day (both teams are aligned and motivated)
- No merge authorization until Phase 4 complete
