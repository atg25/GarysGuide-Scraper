# Sprint 19: Validation, Security Assertions, and PyPack Quality Gates

## Goal

Finalize PyPack MCP server quality by enforcing strict input validation, security-safe failures, and required quality commands.

## Scope

- Reject unknown properties (`additionalProperties: false`).
- Enforce `limit` bounds `0..500`.
- Enforce strict date pattern and `date_from <= date_to`.
- Verify no secret/internal leakage in all error paths.
- Pass pytest, mypy, and ruff gates.

## Validation Rules

- `ai_only`: boolean
- `limit`: required integer `0..500`
- `tags`: optional lowercase string array
- `date_from/date_to`: optional `YYYY-MM-DD`
- reject unknown keys and invalid types

## TDD Plan

### Unit

- Positive: valid minimal and full payloads accepted.
- Negative: rejects unknown fields, invalid types, invalid dates, invalid ranges.
- Negative: error normalization strips stack traces and sensitive internals.

### Integration

- Positive: valid payload reaches adapter and returns stable shape.
- Negative: invalid payload blocked before REST call.
- Negative: REST failures always map to normalized envelope.

### E2E

- Positive: `ListTools` and `CallTool` pass with valid request.
- Negative: invalid request returns deterministic validation failure.

## Quality Checklist (PyPack)

- `poetry run pytest`
- `poetry run mypy src tests`
- `poetry run ruff check .`
- `poetry run ruff format --check .`

## Tasks

1. Add schema validation helper in tool entry path.
2. Add negative tests for each validation/security rule.
3. Add quality gate command section in docs.
4. Add final Phase 1 definition-of-done checklist.

## Exit Criteria

- Phase 1 DoD from PM letter is fully satisfied.
- Quality commands pass with zero warnings.
- MCP server is ready for Midterm_Ordo subprocess integration.
