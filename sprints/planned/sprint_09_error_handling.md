# Sprint 9 — Error Handling: Stop Lying, Stop Swallowing

**Status:** Planned  
**Prerequisite:** Sprint 8 merged  
**Review reference:** Uncle Bob audit, Section III — Error Handling

---

## Goal

Remove two classes of dishonest error handling:

1. `get_events_safe` returning `[]` when the network fails — hiding the failure entirely.
2. The broad `except Exception` catch in `runner_once.py` — hiding bugs behind a generic net.

Replace them with named, specific exceptions that callers can consciously handle.

---

## Rationale

Returning an empty list when the HTTP layer fails is a lie: the caller cannot distinguish "zero
events today" from "we could not reach the server." Silent failures lead to silent data corruption —
the pipeline records a run with `fetched_count=0` and `status=success` when it should record
`status=failure`.

The `# noqa: BLE001` comment in `runner_once.py` is a code smell pointing at itself: the developer
knew the catch was too broad and suppressed the linter rather than fixing the problem. `Exception`
catches `KeyError`, `AttributeError`, `MemoryError`, and programmer mistakes. Only transient
network failures deserve a retry; everything else should propagate normally.

---

## Tasks

### 1. Create `src/garys_nyc_events/exceptions.py`

Define a clean exception hierarchy:

```python
GarysGuideError(Exception)
    ScraperNetworkError(GarysGuideError)
        ScraperTimeoutError(ScraperNetworkError)
    ScraperParseError(GarysGuideError)
    StorageError(GarysGuideError)
```

- `ScraperNetworkError` stores the original `requests.RequestException` as `.cause`.
- `ScraperTimeoutError` is raised specifically for `requests.Timeout`.
- No `requests` import inside `exceptions.py`; the hierarchy must be defined purely in terms of
  Python builtins so that callers do not need to import `requests` to catch them.

---

### 2. Remove `get_events_safe` from `GarysGuideScraper`

Delete the `get_events_safe` method entirely.

- Callers that want safe behavior must explicitly catch `ScraperNetworkError`.
- If a caller wraps the call in a `try/except ScraperNetworkError`, the intent is visible and the
  failure is logged, not silenced.

---

### 3. Remove the module-level `get_events_safe` convenience wrapper from `scraper.py`

Same reasoning as above. Delete it.

Update `__init__.py` to remove the `get_events_safe` export. Document the removal in
`CHANGELOG.md` as a breaking change.

---

### 4. Wrap `requests.RequestException` in `GarysGuideScraper._fetch_html`

In `_fetch_html`:

```python
try:
    response = requests.get(...)
    response.raise_for_status()
    return response.text
except requests.Timeout as exc:
    raise ScraperTimeoutError(f"Timed out fetching {url}") from exc
except requests.RequestException as exc:
    raise ScraperNetworkError(f"Network error fetching {url}") from exc
```

The `requests` import is now encapsulated inside `scraper.py`. No code outside this module needs
to know the HTTP client is `requests`.

---

### 5. Narrow the `except Exception` in `runner_once.py`

Replace:

```python
except Exception as exc:  # noqa: BLE001
```

with:

```python
except ScraperNetworkError as exc:
```

- Only network errors are retriable; this is what `is_transient_error` already checks.
- If a non-network exception escapes (e.g., `PartialScrapeError`, `StorageError`), let it
  propagate. The calling process will log a traceback, which is the correct behavior.
- Remove the `# noqa: BLE001` suppression. It must not reappear.
- Update `is_transient_error` in `scheduler.py` to accept `ScraperNetworkError` in addition to
  (or instead of) `requests.RequestException`, since `requests` should not be referenced outside
  the scraper module going forward.

---

### 6. Update `CHANGELOG.md`

Add an entry noting `get_events_safe` is removed as a breaking change in the next minor version.

---

## Acceptance Criteria

- [ ] `exceptions.py` exists with the four-class hierarchy, zero external imports.
- [ ] `GarysGuideScraper` has no method named `get_events_safe`.
- [ ] `scraper.py` has no module-level function named `get_events_safe`.
- [ ] `_fetch_html` raises `ScraperNetworkError` (not `requests.RequestException`) on network
      failure.
- [ ] `runner_once.py` `except` clause catches only `ScraperNetworkError`, no `# noqa` comment.
- [ ] `grep -rn "noqa: BLE001" src/` returns zero results.
- [ ] `grep -rn "get_events_safe" src/` returns zero results.
- [ ] All existing tests pass (tests that previously asserted on `get_events_safe` behavior must be
      rewritten to assert on `ScraperNetworkError` propagation).

---

## Tests Required

### New tests in `tests/test_scraper_unit.py`

| #   | Name                                                               | Type | What it asserts                                                                 |
| --- | ------------------------------------------------------------------ | ---- | ------------------------------------------------------------------------------- |
| 1   | `test_fetch_html_raises_scraper_network_error_on_connection_error` | Unit | Stub HTTP to raise `requests.ConnectionError` → `ScraperNetworkError` is raised |
| 2   | `test_fetch_html_raises_scraper_timeout_error_on_timeout`          | Unit | Stub HTTP to raise `requests.Timeout` → `ScraperTimeoutError` is raised         |
| 3   | `test_fetch_html_raises_scraper_network_error_on_http_error`       | Unit | Stub HTTP to return 500 → `ScraperNetworkError` is raised                       |
| 4   | `test_scraper_network_error_chains_original_cause`                 | Unit | `exc.__cause__` is the original `requests.RequestException`                     |
| 5   | `test_scraper_has_no_get_events_safe_method`                       | Unit | `hasattr(GarysGuideScraper(), "get_events_safe")` is `False`                    |

### New tests in `tests/test_runner_unit.py` (or existing runner test file)

| #   | Name                                                           | Type | What it asserts                                                                            |
| --- | -------------------------------------------------------------- | ---- | ------------------------------------------------------------------------------------------ |
| 6   | `test_run_once_retries_on_scraper_network_error`               | Unit | `scrape_func` raises `ScraperNetworkError` twice then succeeds; `RunSummary.attempts == 3` |
| 7   | `test_run_once_does_not_retry_non_network_errors`              | Unit | `scrape_func` raises `ValueError`; exception propagates immediately, no retry              |
| 8   | `test_run_once_records_failure_on_unrecoverable_network_error` | Unit | `scrape_func` always raises `ScraperNetworkError`; `RunSummary.status == "failure"`        |

---

## Definition of Done

- All eight new tests pass.
- `grep -rn "noqa: BLE" src/` returns zero results.
- `grep -rn "except Exception" src/` returns zero results.
- The phrase "returning empty list on failure" does not appear in any comment in the codebase.
