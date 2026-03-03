# Sprint 12 — Event Completeness: Location, Description, Time & AI-Week Filter

**Status:** Planned
**Addresses:** Goal 1 — NYC AI events for the upcoming week with date, time, location, and description

---

## Goal

The current `Event` model only carries `title`, `date`, `price`, `url`, and `source`. It is missing
**time**, **location/venue**, and **description** fields. The scraper does not yet filter to
AI-focused events or constrain results to the upcoming seven-day window. This sprint closes both
gaps with a strict TDD cadence.

---

## Rationale

Without time, location, and description a consumer of this tool cannot answer the three basic
questions someone asks before attending an event: *Where? When exactly? What's it about?* The
Gary's Guide events page embeds venue and description text inside each event card — we are already
fetching the HTML and discarding that data. This sprint extracts it.

The AI filter and upcoming-week window narrow the 100+ weekly events down to the handful of relevant
ones, reducing noise and keeping the database lean.

---

## Tasks

### 1. Extend `Event` model (`src/garys_nyc_events/models.py`)

Add four new optional fields with `""` defaults so existing downstream code is not broken:

```python
@dataclass(frozen=True)
class Event:
    title: str
    date: str       # e.g. "Thu Feb 06"
    time: str       # e.g. "7:00 PM"  ← NEW
    location: str   # e.g. "Midtown Manhattan, NYC"  ← NEW
    description: str  # first 280 chars of event body text  ← NEW
    price: str
    url: str
    source: str
```

All new fields default to `""` so code that constructs `Event` without them still works.

---

### 2. Extend scraper HTML extraction (`src/garys_nyc_events/scraper.py`)

Add three private extraction helpers and wire them into `_extract_event_from_element`:

- **`_extract_time(text: str) -> str`** — regex for `H:MM AM/PM` or `HH:MM AM/PM` patterns.
- **`_extract_location(element: Tag) -> str`** — look for a `<span>` or `<td>` whose class or
  text contains venue keywords (`venue`, `location`, `address`, `NYC`). Fall back to empty string.
- **`_extract_description(element: Tag) -> str`** — collect non-link inner text, strip HTML
  artifacts, truncate to 280 characters.

Update `_extract_event_from_element` to populate the new fields.

---

### 3. Add upcoming-week date filter (`src/garys_nyc_events/filters.py`)

```python
def filter_events_upcoming_week(
    events: List[Dict[str, str]],
    today: Optional[date] = None,
) -> List[Dict[str, str]]:
    """Return events whose parsed date falls within [today, today+7)."""
```

- Parse the `date` string using `dateutil.parser.parse` with a year-inference fallback.
- Events whose `date` field is empty or unparseable are **excluded** (fail-closed).
- Accept an injectable `today: date` for deterministic testing.

---

### 4. Add AI keyword filter (`src/garys_nyc_events/filters.py`)

```python
AI_KEYWORDS = frozenset({
    "ai", "artificial intelligence", "machine learning", "ml", "llm",
    "deep learning", "generative ai", "gpt", "nlp", "data science",
    "neural network", "robotics", "computer vision",
})

def filter_ai_events(events: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Keep events whose title or description contains at least one AI keyword."""
```

---

### 5. Wire filters into `runner_once._run_scrape`

After the existing keyword filter, apply `filter_ai_events` when
`config.scraper_search_term == "ai"` (or a new `config.ai_filter: bool` flag), then apply
`filter_events_upcoming_week`.

---

### 6. Update DB schema (`src/garys_nyc_events/storage.py`)

Add `time TEXT`, `location TEXT`, `description TEXT` columns to `product_snapshots` (with `ALTER
TABLE … ADD COLUMN … DEFAULT ''` migration guard for existing DBs).

---

## Acceptance Criteria

- [ ] `Event` has `time`, `location`, `description` fields with `""` defaults.
- [ ] `scraper.parse_events()` returns non-empty `location` for at least one event in the fixture HTML.
- [ ] `filter_events_upcoming_week` excludes events older than today and events more than 7 days out.
- [ ] `filter_ai_events` keeps events matching AI keywords and excludes unrelated events.
- [ ] All existing tests continue to pass unchanged.
- [ ] `python-dateutil` added to `pyproject.toml` dependencies.

---

## Tests Required

### Unit tests — `tests/test_scraper_unit.py`

| # | Name | Pass/Fail | What it asserts |
|---|------|-----------|-----------------|
| U1 | `test_extract_time_finds_seven_pm` | Positive | `_extract_time("Join us Thu Jan 23 at 7:00 PM NYC") == "7:00 PM"` |
| U2 | `test_extract_time_returns_empty_for_no_time` | Negative | `_extract_time("No time here") == ""` |
| U3 | `test_extract_location_returns_venue_text` | Positive | Element with `<span class="venue">Midtown NYC</span>` → `"Midtown NYC"` |
| U4 | `test_extract_location_returns_empty_when_absent` | Negative | Element with no venue markup → `""` |
| U5 | `test_extract_description_truncates_at_280` | Positive | Body text of 500 chars → `len(description) <= 280` |
| U6 | `test_parse_events_includes_time_location_description` | Positive | Fixture HTML → at least one event with non-empty `time` or `location` |

### Unit tests — `tests/test_filter_unit.py`

| # | Name | Pass/Fail | What it asserts |
|---|------|-----------|-----------------|
| U7 | `test_filter_upcoming_week_excludes_yesterday` | Negative | Event dated yesterday is excluded |
| U8 | `test_filter_upcoming_week_includes_tomorrow` | Positive | Event dated tomorrow is included |
| U9 | `test_filter_upcoming_week_excludes_eight_days_out` | Negative | Event 8 days out is excluded |
| U10 | `test_filter_upcoming_week_excludes_empty_date` | Negative | Event with `date: ""` is excluded |
| U11 | `test_filter_ai_events_keeps_ai_title` | Positive | `"NYC AI Summit"` survives the filter |
| U12 | `test_filter_ai_events_drops_non_ai` | Negative | `"Wine & Cheese"` is filtered out |
| U13 | `test_filter_ai_events_matches_description_keyword` | Positive | Non-AI title but description `"machine learning demo"` is kept |

### Integration test — `tests/test_scraper_unit.py`

| # | Name | Pass/Fail | What it asserts |
|---|------|-----------|-----------------|
| I1 | `test_parse_events_fixture_new_fields_present` | Positive | Parsing updated fixture yields dicts with keys `time`, `location`, `description` |
| I2 | `test_run_scrape_applies_ai_and_week_filters` | Positive | Stub scraper returning mix of AI/non-AI events; after `_run_scrape`, only AI + upcoming survive |

### E2E test — `tests/test_e2e_live.py` (marked `@pytest.mark.e2e`)

| # | Name | Pass/Fail | What it asserts |
|---|------|-----------|-----------------|
| E1 | `test_live_ai_events_have_required_fields` | Positive | Live scrape of garysguide.com returns ≥1 event; every event dict has all 8 keys |
| E2 | `test_live_ai_events_all_within_next_seven_days` | Positive | All returned events pass `filter_events_upcoming_week` |
| E3 | `test_live_returns_no_non_ai_events` | Negative | After AI filter, no event's title/description is completely free of AI keywords |

---

## Definition of Done

- All 16 tests listed above pass (E2E tests pass with `pytest -m e2e`).
- `Event` model serializes cleanly to dict via `dataclasses.asdict`.
- No regressions in any existing test.
- `python-dateutil` in `pyproject.toml`.
- Updated `tests/fixtures/sample_events_page.html` to include venue and time markup.
