# Sprint 18: REST API Adapter and Error Normalization (PyPack)

## Goal

Implement thin tool logic that calls existing REST API and always returns normalized MCP-safe output.

## Scope

- Build REST request URL from `GARYS_EVENTS_REST_API_BASE_URL`.
- Apply timeout from `GARYS_EVENTS_REST_API_TIMEOUT_MS`.
- Map REST responses to frozen MCP contract.
- Normalize all failures into `{code, message, retriable}`.
- Do not change existing REST API behavior.

## Stable Retriable Error Taxonomy

- Retriable (`retriable=true`): timeout, HTTP 429, HTTP 503, HTTP 504, network disconnect/reset.
- Non-retriable (`retriable=false`): all other 4xx validation/auth/client errors.
- Unknown/unclassified failures default to non-retriable unless explicitly mapped.

## Adapter Contract

### Input

- Validated query DTO from `query_events` tool.

### Success Output

- `ok: true` with normalized `data.count` and `data.events`.

### Failure Output

- `ok: false` with stable `error.code`, `error.message`, `error.retriable`.

## TDD Plan

### Unit

- Positive: query params map correctly for all supported filters.
- Positive: successful REST JSON maps to normalized MCP success shape.
- Negative: missing base URL returns config error.
- Negative: timeout returns normalized retriable error.
- Negative: 429/503/504 map to normalized retriable errors.
- Negative: representative 4xx client errors map to non-retriable errors.
- Negative: non-JSON payload returns safe parse error.
- Negative: raw upstream/internal exception strings are never exposed.

### Integration

- Positive: adapter works against local REST API instance.
- Negative: non-2xx response is normalized.
- Negative: REST service down returns safe retriable failure.

### E2E

- Positive: MCP `CallTool` returns normalized payload through adapter.
- Negative: REST endpoint unavailable returns normalized failure envelope.

## Tasks

1. Implement adapter call utility in `mcp/tools/query_events.py`.
2. Add centralized error mapping helper.
3. Add timeout parsing/default helper.
4. Wire adapter into `CallTool` execution path.

## Exit Criteria

- Tool path depends only on existing REST API.
- Success and failure outputs match contract snapshots.
- Error output contains no secrets, stack traces, or internals.
- Retriable/non-retriable classification is deterministic and tested.
