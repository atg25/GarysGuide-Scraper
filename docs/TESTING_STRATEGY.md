# Testing Strategy

## Unit Tests

- No network I/O.
- No filesystem I/O unless using temporary in-memory or temp-dir fixtures.
- Use stubs/spies/doubles (for example `tests/http_doubles.py`).
- Fast enough to run on each save.

## Integration Tests

- Must exercise real component boundaries (for example, SQLite integration against an actual DB file).
- Must not mock HTTP library internals (`requests_mock` is unit-test-only behavior).
- Can run in normal CI job.

## End-to-End (E2E) Tests

- May hit live endpoints (GarysGuide) and therefore are opt-in.
- Tagged with `@pytest.mark.e2e` and excluded unless explicitly enabled.
- Run in scheduled CI or manual verification pipelines.
