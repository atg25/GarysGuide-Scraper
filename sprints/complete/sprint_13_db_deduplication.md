# Sprint 13 — DB Deduplication: Zero Repeating Events

**Status:** Planned
**Addresses:** Goal 2 — 0 repeating events in the database

---

## Goal

Guarantee that the same real-world event is stored **exactly once** in the database regardless of
how many times the scraper runs. Today the `products` table already deduplicates by `canonical_key`
(URL or title), but `product_snapshots` grows a new row for the same event on every run, and
`products` itself can drift to multiple rows if the canonical key construction is inconsistent.
This sprint closes both gaps and adds a `fetch_events` read-path that prevents duplicate events
from reaching any consumer.

---

## Rationale

The current design was built for a "Product Hunt snapshot" mental model — capturing point-in-time
vote counts. For an events tool, the goal is fundamentally different: each event is a unique datum
that we want to enrich over time, not snapshot repeatedly. Each re-scrape of the same event should
**update** the existing record (upsert), not append a new one.

Two guarantees are needed:
1. **Write-path guarantee** — `persist_run` must not produce duplicate `products` rows for the same
   event and must not create a new `product_snapshots` row if the event already has one from a prior
   run (only update the latest metadata/tags).
2. **Read-path guarantee** — `fetch_events()` returns a list where every event URL (or title, if no
   URL) is unique.

---

## Tasks

### 1. Redefine the deduplication key (`src/garys_nyc_events/storage.py`)

- Current: `canonical_key = "url:<url>"` or `"name:<title>"`.
- Change: normalise URLs by stripping query parameters and fragment identifiers before keying, so
  `https://garysguide.com/events/123?ref=email` and `https://garysguide.com/events/123` resolve to
  the same key.
- Add a `_normalize_url(url: str) -> str` helper using `urllib.parse.urlparse`.

### 2. Add upsert-or-skip snapshot logic

Replace the current `INSERT OR REPLACE INTO product_snapshots` with an upsert that only writes
when the event is **new** (first time seen) or when key fields have changed (price, date, location):

```sql
INSERT INTO product_snapshots (run_id, product_id, price, event_date, time, location, description, observed_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(product_id) DO UPDATE SET
    price      = excluded.price,
    event_date = excluded.event_date,
    time       = excluded.time,
    location   = excluded.location,
    description= excluded.description,
    observed_at= excluded.observed_at
WHERE excluded.event_date != product_snapshots.event_date
   OR excluded.price      != product_snapshots.price
   OR excluded.location   != product_snapshots.location;
```

- Change the `UNIQUE(run_id, product_id)` constraint to `UNIQUE(product_id)` so only one snapshot
  per event is ever live.
- **Schema migration** — add `ALTER TABLE product_snapshots DROP CONSTRAINT` / recreate logic
  inside `init_schema` with a version-guard so existing databases upgrade cleanly.

### 3. Add `fetch_events` read-path (`src/garys_nyc_events/storage.py`)

```python
def fetch_events(
    self,
    *,
    limit: int = 0,
    ai_only: bool = False,
) -> List[Dict[str, str]]:
    """Return unique events ordered by event_date ASC.
    Joins products + latest product_snapshots.
    If ai_only=True, only rows whose title or description contains an AI keyword.
    """
```

This replaces any ad-hoc SELECT callers. The JOIN uses `product_id` so no event can appear twice.

### 4. Add `EventStore.fetch_events` to protocol (`src/garys_nyc_events/protocols.py`)

```python
def fetch_events(self, *, limit: int = 0, ai_only: bool = False) -> List[Dict[str, str]]: ...
```

### 5. Add `SCRAPER_DEDUP_WINDOW_DAYS` config option (`src/garys_nyc_events/config.py`)

An optional integer (default `0` = no window) that prevents re-inserting an event seen within the
last N days. Useful for very frequent scheduling.

---

## Acceptance Criteria

- [ ] Inserting the same event twice with the same URL produces exactly 1 `products` row and 1
      `product_snapshots` row.
- [ ] Running `persist_run` 10× with the same 5-event list leaves exactly 5 rows in `products` and
      5 rows in `product_snapshots`.
- [ ] `fetch_events()` never returns two dicts with the same `url` (or same `title` when url is
      empty).
- [ ] Existing `test_dedupe_upsert_by_url` continues to pass.
- [ ] The schema migration does not error on a fresh DB or an existing DB from Sprint 12.

---

## Tests Required

### Unit tests — `tests/test_storage_unit.py`

| # | Name | Pass/Fail | What it asserts |
|---|------|-----------|-----------------|
| U1 | `test_same_event_twice_produces_one_product_row` | Positive | `persist_run` called twice with same event → `count_rows("products") == 1` |
| U2 | `test_same_event_twice_produces_one_snapshot_row` | Positive | Same as above → `count_rows("product_snapshots") == 1` |
| U3 | `test_url_normalization_strips_query_params` | Positive | URLs `…/123?ref=a` and `…/123?ref=b` map to same canonical key |
| U4 | `test_url_normalization_strips_fragment` | Positive | `…/123#section` and `…/123` map to same key |
| U5 | `test_ten_runs_same_five_events_still_five_rows` | Positive | 10× `persist_run` with same list → `products == 5`, `snapshots == 5` |
| U6 | `test_updated_price_overwrites_snapshot` | Positive | Second run with different price updates the single snapshot row |
| U7 | `test_distinct_events_each_get_own_row` | Positive | 3 events with different URLs → 3 `products`, 3 `snapshots` |
| U8 | `test_fetch_events_returns_no_duplicates` | Positive | Fill DB with 2 events, 5 runs each → `len(fetch_events()) == 2` |
| U9 | `test_fetch_events_ai_only_filters_correctly` | Positive | 3 events (2 AI, 1 cooking) → `fetch_events(ai_only=True)` returns 2 |
| U10 | `test_fetch_events_ai_only_returns_empty_for_no_matches` | Negative | DB contains only non-AI events → `fetch_events(ai_only=True) == []` |

### Integration tests — `tests/test_storage_unit.py`

| # | Name | Pass/Fail | What it asserts |
|---|------|-----------|-----------------|
| I1 | `test_persist_run_idempotent_across_schema_reinit` | Positive | Call `init_schema` twice on same DB, then write 3 events → 3 rows, no errors |
| I2 | `test_schema_migration_preserves_existing_data` | Positive | Write 2 events to a v1 schema DB, call `init_schema` (migrate), then `fetch_events` returns 2 |

### E2E test — `tests/test_e2e_live.py` (marked `@pytest.mark.e2e`)

| # | Name | Pass/Fail | What it asserts |
|---|------|-----------|-----------------|
| E1 | `test_live_two_runs_no_duplicate_products` | Positive | Run scraper twice into same DB → `count_rows("products") == count_rows("product_snapshots")` |
| E2 | `test_live_fetch_events_unique_urls` | Positive | After live run, `len(fetch_events())` equals `len({e["url"] for e in fetch_events()})` |
| E3 | `test_persist_run_with_duplicate_url_different_title` | Negative | Two events: same URL, different title → 1 product row, keyed on URL |

---

## Definition of Done

- All 15 tests pass.
- `product_snapshots` has a `UNIQUE(product_id)` constraint (confirmed by `PRAGMA table_info`).
- `fetch_events()` is the canonical read-path; no raw SQL SELECTs outside `storage.py`.
- No regressions in any prior sprint's tests.
