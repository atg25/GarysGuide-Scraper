# Sprint Plan: Gary's Guide NYC Events Scraper

This project follows a Test-Driven Development (TDD) approach. Each sprint includes positive and negative Unit, Integration, and End-to-End (E2E) tests.

## Sprint 1: Foundation & Environment Setup

**Goal:** Initialize the project structure, configure Poetry, and establish the testing framework.

- **Tasks:**
  - [x] Initialize Poetry project with `src/` layout.
  - [x] Configure Poetry for packaging and PyPI publishing.
  - [x] Setup `pyproject.toml` dependencies (`beautifulsoup4`, `requests`, `pytest`, `pytest-cov`).
  - [x] Create `.gitignore`.
  - [x] Create basic package structure (`src/garys_nyc_events`).
  - [x] Setup `tests/` directory structure.
- **Tests:**
  - _Unit:_ Verify package version import.
  - _Integration:_ Verify build artifacts are generated successfully.

## Sprint 2: Core Web Scraper (TDD)

**Goal:** Implement the primary scraper for `garysguide.com/events`.

- **Tasks:**
  - [x] define `Event` data class/structure.
  - [x] Implement `fetch_page` with `User-Agent` and error handling.
  - [x] Implement `parse_event_row` to extract Title, Date, Price, and Venue/Location.
  - [x] Implement polite delays (throttling).
- **Tests:**
  - _Unit (Negative):_ Test `fetch_page` with 404/500 errors (mocked).
  - _Unit (Positive):_ Test `parse_event_row` with sample HTML snippets.
  - _Integration:_ Mocked HTTP session returning a full page file, verify list extraction.

## Sprint 3: Newsletter Fallback Parser

**Goal:** Create the fallback parser for raw HTML (email/newsletter context).

- **Tasks:**
  - [x] Implement `parse_newsletter_html` function.
  - [x] handle slight structure variations (email HTML often differs from web HTML).
- **Tests:**
  - _Unit (Positive):_ Test parsing against a saved sample email HTML.
  - _Unit (Negative):_ Test parsing against malformed HTML or non-event HTML.

## Sprint 4: Robustness & End-to-End

**Goal:** Finalize the public API and ensure scraper resilience.

- **Tasks:**
  - [x] Create main entry point `get_events()`.
  - [x] Refactor for clean exception handling.
  - [x] Ensure `src` layout is properly discoverable.
- **Tests:**
  - _E2E (Positive):_ Run against the live site (carefully, once) or a high-fidelity local mirror to verify full flow.
  - _E2E (Negative):_ Simulate blocking/availability issues.

## Sprint 5: Packaging & Documentation

**Goal:** Prepare for distribution.

- **Tasks:**
  - [x] Write `README.md` with usage examples.
  - [x] Finalize `pyproject.toml` metadata.
  - [x] Verify build artifacts (`sdist` and `wheel`).
- **Tests:**
  - _Integration:_ Install built wheel in a fresh virtualenv and run a basic import test.

---

## Upcoming Sprints (TDD — Tests Written First)

### Sprint 12: Event Completeness — Location, Description, Time & AI-Week Filter

**Goal:** Add `time`, `location`, and `description` to `Event`; filter to AI events in the
upcoming 7-day window. Addresses **Goal 1**.

- **Tasks:**
  - [ ] Extend `Event` dataclass with `time`, `location`, `description` fields (defaults `""`).
  - [ ] Add `_extract_time`, `_extract_location`, `_extract_description` to `GarysGuideScraper`.
  - [ ] Add `filter_events_upcoming_week(events, today)` to `filters.py`.
  - [ ] Add `filter_ai_events(events)` with `AI_KEYWORDS` frozenset to `filters.py`.
  - [ ] Wire both filters into `runner_once._run_scrape`.
  - [ ] Add `time`, `location`, `description` columns to `product_snapshots` schema.
  - [ ] Add `python-dateutil` dependency.
- **Tests (write first):**
  - _Unit (×13):_ Time/location/description extraction; AI keyword filter positive & negative; week
    window filter boundary cases (yesterday excluded, tomorrow included, 8 days excluded, empty
    date excluded).
  - _Integration (×2):_ Fixture HTML → new fields present; stub scraper → AI+week filter applied.
  - _E2E (×3):_ Live scrape → required fields present; all events within next 7 days; no non-AI
    events leak through.
- **Detail:** `sprints/planned/sprint_12_event_completeness.md`

---

### Sprint 13: DB Deduplication — Zero Repeating Events

**Goal:** Guarantee the same event is stored exactly once regardless of how many times the scraper
runs. Addresses **Goal 2**.

- **Tasks:**
  - [ ] Normalise canonical keys (strip URL query params / fragments).
  - [ ] Change `product_snapshots` constraint from `UNIQUE(run_id, product_id)` → `UNIQUE(product_id)`.
  - [ ] Use upsert-or-skip snapshot logic (only update when price/date/location changes).
  - [ ] Add `fetch_events(limit, ai_only)` read-path method to `SQLiteEventStore`.
  - [ ] Add `fetch_events` to `EventStore` protocol.
  - [ ] Schema migration guard for existing databases.
- **Tests (write first):**
  - _Unit (×10):_ Same event twice → 1 product row, 1 snapshot row; URL normalisation; 10 runs
    same 5 events → 5 rows; price update overwrites snapshot; `fetch_events` uniqueness guarantee.
  - _Integration (×2):_ Idempotent schema reinit; migration preserves existing data.
  - _E2E (×3):_ Live two-run → no duplicate products; `fetch_events` unique URLs; same-URL
    different-title → 1 product keyed on URL.
- **Detail:** `sprints/planned/sprint_13_db_deduplication.md`

---

### Sprint 14: Gemini AI Tagging — Automated Event Tags

**Goal:** Call the Google Gemini API after each scrape to attach semantic tags to every event.
Addresses **Goal 3**. Key lives in `.env` as `GEMINI_API_KEY` (also accepts legacy `GEMNINI_API_KEY`).

- **Tasks:**
  - [ ] Add `tags: List[str]` field to `Event` model (default `[]`).
  - [ ] Create `src/garys_nyc_events/tagger.py` with `GeminiTagger` class.
  - [ ] Implement `_call_gemini` via existing `HttpClient` protocol (no Google SDK dep required).
  - [ ] Add `gemini_api_key` and `tagging_enabled` to `PipelineConfig`.
  - [ ] Wire tagger into `runner_once._run_scrape` (optional, fail-safe).
  - [ ] Add `tags TEXT` column to `product_snapshots`; deserialise in `fetch_events`.
  - [ ] Deprecation warning when `GEMNINI_API_KEY` (typo) is used; migrate `.env` to `GEMINI_API_KEY`.
- **Tests (write first):**
  - _Unit (×9):_ No key → `[]`; network failure → `[]`; malformed JSON → `[]`; valid response →
    list; truncation; fallback env var; `TAGGING_ENABLED=false` bypasses calls.
  - _Integration (×3):_ Tags persisted & retrieved; empty tags stored as `[]`; schema migration safe.
  - _E2E (×3):_ Live key → non-empty tags; tags are lowercase strings; pipeline runs without key.
- **Detail:** `sprints/planned/sprint_14_gemini_ai_tagging.md`

---

### Sprint 15: Public REST API — NYC AI Events as a Service

**Goal:** Expose the database as a FastAPI REST API consumable by any HTTP client. Addresses
**Goal 4**.

- **Tasks:**
  - [ ] Create `src/garys_nyc_events/api/` package (app factory, auth, routers, schemas).
  - [ ] `GET /health` — public; `GET /events` — bearer auth; `GET /events/{id}` — bearer auth.
  - [ ] `GET /runs` — list recent runs; `POST /runs/trigger` — manual scrape trigger.
  - [ ] Pydantic `EventOut` / `EventListOut` / `RunOut` response schemas.
  - [ ] Bearer token auth via `API_TOKEN` env var; open mode (read-only) when unset.
  - [ ] Add FastAPI/uvicorn/httpx/pydantic≥2 dependencies.
  - [ ] API server entrypoint in `Dockerfile`; port `8000` in `docker-compose.yml`.
  - [ ] OpenAPI/Swagger UI at `/docs`.
- **Tests (write first):**
  - _Unit (×12):_ Health no-auth; missing/invalid token → 401/403; valid token → event list;
    `ai_only`/date-range/tag filters; `GET /events/{id}` 404; trigger 503 (no token configured);
    trigger 202; runs list.
  - _Integration (×4):_ Full pipeline → events visible via API; trigger persists events; dedup
    across two triggers; tags in response.
  - _E2E (×5):_ Live health; live AI events; trigger then fetch; invalid token blocked; OpenAPI
    JSON valid.
- **Detail:** `sprints/planned/sprint_15_rest_api.md`
