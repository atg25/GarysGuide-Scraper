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
