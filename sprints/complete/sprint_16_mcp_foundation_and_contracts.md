# Sprint 16: MCP Foundations and Contract Freeze (PyPack)

## Goal

Lock the MCP contract and baseline behavior for `garys_events.query_events` before coding server runtime.

## Scope

- Keep existing REST API behavior unchanged.
- Define stable tool identity and request/response contract.
- Define normalized error envelope.
- Define only the PM-approved PyPack env vars.
- Add baseline tests to prevent regressions.

## Tool Identity

- Name: `garys_events.query_events`
- Stability rule: do not rename after first release.
- Transport target: stdio subprocess (implemented in Sprint 17).

## Contract

### Input

- `ai_only`: boolean (default `true`)
- `limit`: integer `0..500`
- `tags`: optional array of lowercase strings
- `date_from`: optional `YYYY-MM-DD`
- `date_to`: optional `YYYY-MM-DD`

### Success Output

- `ok`: `true`
- `data.count`: integer
- `data.events`: array of normalized events

### Failure Output

- `ok`: `false`
- `error.code`: stable machine code
- `error.message`: safe user-facing message
- `error.retriable`: boolean

## Environment Variables (PyPack)

- `GARYS_EVENTS_REST_API_BASE_URL`
- `GARYS_EVENTS_REST_API_TIMEOUT_MS` (default `10000`)
- `GARYS_EVENTS_MCP_ENABLED` (default `true`)

## TDD Plan

### Unit

- Positive: accepts minimal and full valid payloads.
- Negative: rejects unknown fields, invalid dates, and out-of-range `limit`.

### Integration

- Positive: API baseline snapshot for existing endpoints remains stable.
- Negative: existing auth failure paths remain unchanged.

### E2E

- Positive: API smoke behavior unchanged before MCP runtime work.
- Negative: invalid token path remains safe and unchanged.

## Tasks

1. Add contract fixtures for input/success/failure.
2. Add baseline regression tests for existing API outputs.
3. Document contract and env var defaults.
4. Add sprint sign-off checklist.

## Exit Criteria

- Contract is frozen in tests and docs.
- Baseline API regression tests pass.
- No production API behavior changes.
