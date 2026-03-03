# Sprint 6 — Dependency Inversion: Define and Inject Abstractions

**Status:** Active  
**Review reference:** Uncle Bob audit, Section I — Dependency Inversion Principle (DIP)

---

## Goal

Eliminate the hard dependency between `runner_once.py` (high-level policy) and the concrete classes
`GarysGuideScraper` and `SQLiteEventStore` (low-level details). The runner must depend only on
abstractions it defines. Concrete types move down to the application wiring layer.

---

## Rationale

`run_once()` currently imports `SQLiteEventStore` directly and accepts it as a typed parameter.
`_build_scraper()` constructs a `GarysGuideScraper` from inside the module. This means:

- Swapping the storage engine (e.g., Postgres, in-memory) requires changing runner code.
- Swapping the HTTP-backed scraper for a file-based stub requires patching internals.
- The runner cannot be unit-tested without touching real SQLite or the real network.

Uncle Bob's rule: _"High-level modules should not depend on low-level modules. Both should depend on
abstractions."_

---

## Tasks

### 1. Create `src/garys_nyc_events/protocols.py`

Define two `typing.Protocol` classes:

**`EventScraper`**

```python
class EventScraper(Protocol):
    def get_events(self) -> List[Dict[str, str]]: ...
```

**`EventStore`**

```python
class EventStore(Protocol):
    def init_schema(self) -> None: ...
    def record_run(...) -> RunRecord: ...
    def save_events(...) -> None: ...
```

- Use `@runtime_checkable` on both so `isinstance` checks work in tests.
- Import nothing from `scraper.py` or `storage.py` inside this module. The protocols must not pull
  in concrete implementations.

---

### 2. Update `runner_once.py` — depend on protocols, not concrete types

- Change the `store` parameter of `run_once()` from `Optional[SQLiteEventStore]` to
  `Optional[EventStore]`.
- Remove the `SQLiteEventStore` import from the top-level import block; move it to only appear
  inside `_default_store()` factory function at the bottom of the module.
- Change `_build_scraper()` to return `EventScraper` (the protocol type), not `GarysGuideScraper`.
- Remove the `GarysGuideScraper` import from the top-level block; it belongs only in the scraper
  factory.
- The type annotation on `scrape_func` already uses `Callable`; keep it, but ensure it matches the
  `EventScraper` protocol signature.

---

### 3. Wire concrete types at the entry point only

- In `runner_once.py`, add a private `_default_store(cfg: PipelineConfig) -> EventStore` factory
  that constructs `SQLiteEventStore`. This is the only place `SQLiteEventStore` is referenced.
- In `runner_once.py`, add a private `_default_scraper(cfg: PipelineConfig) -> EventScraper`
  factory that constructs `GarysGuideScraper`. This is the only place `GarysGuideScraper` appears
  in this module.

---

### 4. Expose protocols in `__init__.py`

Add `EventScraper` and `EventStore` to the public re-exports in
`src/garys_nyc_events/__init__.py` so downstream code can type-hint against them without importing
from `protocols` directly.

---

## Acceptance Criteria

- [ ] `protocols.py` exists and contains only `Protocol` definitions. Zero concrete imports.
- [ ] `runner_once.py` top-level imports contain no reference to `SQLiteEventStore` or
      `GarysGuideScraper`.
- [ ] `run_once()` signature uses `EventStore` and `EventScraper` (or `Callable`) as parameter
      types, not concrete classes.
- [ ] Passing a custom `EventStore` stub to `run_once()` in tests requires zero patching of
      internals (no `monkeypatch`, no `mock.patch`).
- [ ] `mypy` reports zero new errors after the change (run with `--strict` on the affected modules).
- [ ] All existing tests continue to pass without modification.

---

## Tests Required

### Unit tests (additions to `tests/test_storage_unit.py` and a new `tests/test_protocols_unit.py`)

| #   | Name                                                        | Type | What it asserts                                                                                                                                                 |
| --- | ----------------------------------------------------------- | ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `test_sqlite_store_satisfies_event_store_protocol`          | Unit | `isinstance(SQLiteEventStore(":memory:"), EventStore)` is `True`                                                                                                |
| 2   | `test_garys_guide_scraper_satisfies_event_scraper_protocol` | Unit | `isinstance(GarysGuideScraper(), EventScraper)` is `True`                                                                                                       |
| 3   | `test_run_once_accepts_in_memory_stub_store`                | Unit | Inject a hand-written `StubEventStore` (pure Python dict, no SQLite). `run_once()` completes without error. Verify `StubEventStore.record_run` was called once. |
| 4   | `test_run_once_accepts_stub_scraper`                        | Unit | Inject a `StubEventScraper` that returns a fixed list of two events. Assert `RunSummary.fetched_count == 2`. No network calls.                                  |
| 5   | `test_run_once_does_not_import_sqlite_at_module_level`      | Unit | Use `ast.parse` + `ast.walk` to assert that no `import sqlite3` or `from .storage import SQLiteEventStore` appears at module scope in `runner_once.py`.         |

---

## Definition of Done

- All five new tests pass.
- `mypy --strict src/garys_nyc_events/runner_once.py src/garys_nyc_events/protocols.py` exits 0.
- A reviewer can read `runner_once.py` top-level imports and see no concrete storage or scraper
  class referenced there.
