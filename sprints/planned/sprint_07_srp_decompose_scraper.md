# Sprint 7 — Single Responsibility: Decompose `scraper.py`

**Status:** Planned  
**Prerequisite:** Sprint 6 merged  
**Review reference:** Uncle Bob audit, Section I (SRP) and Section II (naming, `to_dict`)

---

## Goal

`scraper.py` currently holds four distinct responsibilities: the data model, HTTP scraping, keyword
filtering, and AI-specific JSON formatting. Each responsibility must live in its own module.
The module-level `get_events()` name-shadow and the `Event.to_dict()` method must also be
eliminated.

---

## Rationale

A module with four distinct jobs has four reasons to change. If the AI JSON format changes, or the
filtering algorithm changes, a reviewer must read the scraper to understand an unrelated concern.
Uncle Bob's rule: _"A class should have only one reason to change."_ The same applies to modules.

The shadowing issue (`get_events` appears as both a class method and a module-level function on
consecutive lines) is a readability trap — a new engineer will not know which one they are calling.

`Event.to_dict()` encodes serialization knowledge inside a data structure. Data structures should be
transparent bags of values. Serialization belongs to the presentation/use-case layer.

---

## Tasks

### 1. Create `src/garys_nyc_events/models.py`

Move the `Event` dataclass here. This is its only reason to change: the shape of a scraped event
record.

- Remove `to_dict()` from `Event`.
- Remove the `asdict` import from `scraper.py` (it is no longer needed there).
- Update every current call site of `event.to_dict()` to use `dataclasses.asdict(event)` instead.
  Call sites to update: `scraper.py::parse_events`, `scraper.py::parse_newsletter_html`.

---

### 2. Create `src/garys_nyc_events/filters.py`

Move `filter_events_by_keyword` here. Its only reason to change: the filtering strategy.

- The function signature and behavior are unchanged.
- Remove `filter_events_by_keyword` from `scraper.py`.
- Update the import in `runner_once.py` from `from .scraper import … filter_events_by_keyword` to
  `from .filters import filter_events_by_keyword`.

---

### 3. Create `src/garys_nyc_events/formatters.py`

Move `get_events_ai_json` here. Its only reason to change: how events are serialized for an
AI consumer.

- `formatters.py` imports from `filters.py` and calls the `EventScraper` protocol (not
  `GarysGuideScraper` directly) — or accepts a pre-fetched event list so it stays pure.
  Preferred: accept `List[Dict[str, str]]` so the formatter has zero I/O dependency.
- Remove `get_events_ai_json` from `scraper.py`.

---

### 4. Create `src/garys_nyc_events/newsletter_parser.py`

Move `parse_newsletter_html` here. Its only reason to change: the HTML structure of Gary's Guide
newsletter emails.

- The function signature and behavior are unchanged.
- Remove `parse_newsletter_html` from `scraper.py`.
- Update `tests/test_newsletter_parser_unit.py` import path.

---

### 5. Rename the module-level `get_events()` in `scraper.py`

Rename to `scrape_default_garys_guide(delay_seconds: float = 1.5) -> List[Dict[str, str]]`.

- Same rename for `get_events_safe` → `scrape_default_garys_guide_safe` (this function is slated
  for removal in Sprint 9; keep the rename here so it is clearly marked as deprecated).
- Update `__init__.py` to export the new name and add a `__deprecated__` alias if backward
  compatibility is required for the current public API version.

---

### 6. Update `__init__.py` public re-exports

Ensure the public API surface (`from garys_nyc_events import …`) re-exports:

- `Event` (from `models`)
- `filter_events_by_keyword` (from `filters`)
- `parse_newsletter_html` (from `newsletter_parser`)
- `scrape_default_garys_guide` (from `scraper`)
- All `Protocol` types from Sprint 6

Remove any re-exports of the old names after confirming no external callers exist.

---

## Acceptance Criteria

- [ ] `scraper.py` contains only: constants, `GarysGuideScraper` class, and
      `scrape_default_garys_guide` / `scrape_default_garys_guide_safe` convenience wrappers.
- [ ] `models.py` exists and `Event` has no `to_dict()` method.
- [ ] `filters.py` exists and contains `filter_events_by_keyword`.
- [ ] `formatters.py` exists and contains `get_events_ai_json` (or equivalent).
- [ ] `newsletter_parser.py` exists and contains `parse_newsletter_html`.
- [ ] Zero uses of `.to_dict()` remain in the codebase; all replaced with `dataclasses.asdict()`.
- [ ] Zero uses of the old module-level `get_events()` name remain.
- [ ] `grep -r "from .scraper import.*filter_events_by_keyword" src/` returns no results.
- [ ] All existing tests pass without modification (import paths in tests updated as needed).

---

## Tests Required

### New / updated tests

| #   | Name                                                           | Type | What it asserts                                                                                    |
| --- | -------------------------------------------------------------- | ---- | -------------------------------------------------------------------------------------------------- |
| 1   | `test_event_has_no_to_dict_method`                             | Unit | `hasattr(Event(...), "to_dict")` is `False`                                                        |
| 2   | `test_asdict_produces_expected_keys`                           | Unit | `dataclasses.asdict(Event(...))` returns dict with keys `title, date, price, url, source`          |
| 3   | `test_filter_events_by_keyword_is_importable_from_filters`     | Unit | `from garys_nyc_events.filters import filter_events_by_keyword` succeeds                           |
| 4   | `test_parse_newsletter_html_importable_from_newsletter_parser` | Unit | `from garys_nyc_events.newsletter_parser import parse_newsletter_html` succeeds                    |
| 5   | `test_scraper_module_does_not_define_filter_function`          | Unit | `import inspect, garys_nyc_events.scraper as m; assert not hasattr(m, "filter_events_by_keyword")` |
| 6   | `test_get_events_ai_json_importable_from_formatters`           | Unit | `from garys_nyc_events.formatters import get_events_ai_json` succeeds                              |

---

## Definition of Done

- All new and existing tests pass.
- `scraper.py` line count drops by at least 40%.
- A single `grep -n "def " src/garys_nyc_events/scraper.py` reveals only
  `GarysGuideScraper` methods and the two renamed module-level wrappers.
