# Sprint 21: Midterm_Ordo Chat Tool Descriptor and Role Controls (Optional)

## Goal

Register optional chat descriptor for `garys_events.query_events` with least-privilege role visibility.

## Scope

- Create descriptor in `src/core/use-cases/tools/garys-events-query.tool.ts`.
- Run dot-name compatibility check before descriptor registration.
- Register in `src/lib/chat/tool-composition-root.ts` using canonical name or alias result from that check.
- Enforce role allowlist and blocked-role behavior.
- Validate whether chat tool names allow dots.
- Keep canonical MCP name `garys_events.query_events`; if dots are unsupported, expose chat alias `garys_events_query_events` with deterministic mapping to the canonical MCP name.

## Required Descriptor Fields

- `name: "garys_events.query_events"` when dots are supported, otherwise `name: "garys_events_query_events"`
- schema description and input schema with `additionalProperties: false`
- `command: new GarysEventsQueryCommand()`
- `roles: ["AUTHENTICATED", "STAFF", "ADMIN"]` (or stricter)
- `category: "search"`

## Deterministic Name Mapping Rule

- `garys_events_query_events` (chat alias) maps to `garys_events.query_events` (MCP canonical).
- Mapping is one-to-one and centralized in one helper.
- Role policy attaches to chat-visible name, but execution always targets canonical MCP name.

## TDD Plan

### Unit

- Positive: descriptor validates and name is exact.
- Positive: allowed roles see tool in schema retrieval.
- Negative: disallowed roles do not see tool.
- Negative: role in request payload does not bypass middleware policy.
- Negative: alias mapping cannot resolve to unknown/alternate MCP names.

### Integration

- Positive: descriptor registration is active in composition root.
- Negative: missing registration fails tool discovery tests.
- Negative: unauthorized role is blocked on execution.
- Positive: tool-count expectation is updated after registration.
- Positive: role visibility expectation matrix is updated and enforced.

### E2E

- Positive: allowed-role chat call executes through MCP subprocess.
- Negative: blocked role receives safe normalized denial/error response.

## Tasks

1. Implement descriptor file in Midterm_Ordo.
2. Add dot-name compatibility check and alias helper.
3. Register descriptor in composition root after compatibility decision.
4. Add role-based visibility and tool-count tests.
5. Add chat integration docs for env vars and toggles.

## Exit Criteria

- Descriptor is optional but complete when enabled.
- Role visibility and blocking are tested.
- Chat can invoke tool through subprocess for allowed roles.
- Dot-name compatibility path (native or alias fallback) is tested and deterministic.
