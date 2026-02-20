# garys_nyc_events

A Python package for scraping NYC tech events from [GarysGuide](https://www.garysguide.com/events), filtering them by keyword, and persisting them to a local SQLite database — all in a single command or Python call.

---

## What This Tool Does

- **Scrapes** the GarysGuide NYC events page and extracts structured event data
- **Filters** events by keyword (e.g. "AI", "Python", "startup")
- **Persists** every run and its results to a local SQLite database with full history
- **Formats** filtered events as clean JSON ready for downstream use (e.g. feeding an AI pipeline)
- **Parses newsletter HTML** as a fallback data source when live scraping is not possible
- **Retries automatically** on transient network errors with configurable backoff
- **Runs as a one-shot container** — schedule it externally with cron or Kubernetes

Each event contains five fields:

| Field    | Example                                   |
| -------- | ----------------------------------------- |
| `title`  | `"AI Demo Night at Cornell Tech"`         |
| `date`   | `"Wed, Mar 5"`                            |
| `price`  | `"FREE"` or `"$25"`                       |
| `url`    | `"https://www.garysguide.com/events/..."` |
| `source` | `"web"` or `"newsletter_fallback"`        |

---

## Install

```bash
pip install garys_nyc_events
```

Or, for local development with [Poetry](https://python-poetry.org/):

```bash
poetry install
```

---

## Usage

### One-liner: scrape all events right now

```python
from garys_nyc_events import scrape_default_garys_guide

events = scrape_default_garys_guide(delay_seconds=1.5)
# returns a list of dicts: [{"title": ..., "date": ..., "price": ..., "url": ..., "source": ...}, ...]
```

### Scrape with the class (more control)

```python
from garys_nyc_events import GarysGuideScraper

scraper = GarysGuideScraper(
    delay_seconds=1.0,    # wait between requests (be polite)
    timeout_seconds=10,   # per-request timeout
)
events = scraper.get_events()
```

### Filter events by keyword

```python
from garys_nyc_events import filter_events_by_keyword

ai_events = filter_events_by_keyword(events, "AI")
# case-insensitive title match — returns only matching events
```

### Export filtered events as JSON

```python
from garys_nyc_events import get_events_ai_json

json_str = get_events_ai_json(events, keyword="AI")
print(json_str)
# Pretty-printed JSON array of AI-related events
```

### Parse a newsletter HTML export (fallback)

If you have a GarysGuide newsletter saved as HTML (e.g. from your email client), you can extract events from it without making any network requests:

```python
from garys_nyc_events import parse_newsletter_html

with open("newsletter.html") as f:
    raw_html = f.read()

events = parse_newsletter_html(raw_html)
# Returns event dicts with source="newsletter_fallback"
# Automatically skips unsubscribe, social, and sponsor links
```

### Run the full pipeline (scrape + persist to SQLite)

```bash
DB_PATH=./local_events.db poetry run garys-events-run-once
```

This will:

1. Scrape GarysGuide
2. Apply any configured keyword filter and event limit
3. Save the run metadata and all events to `local_events.db`
4. Print a summary

Verify the database afterward:

```bash
DB_PATH=./local_events.db ./scripts/verify_db.sh
```

---

## Configuration

All settings are controlled via environment variables. No config files needed.

| Variable                | Default                 | What it does                                         |
| ----------------------- | ----------------------- | ---------------------------------------------------- |
| `DB_PATH`               | `/data/garys_events.db` | Path to the SQLite database file                     |
| `SCRAPER_SEARCH_TERM`   | _(none)_                | Keyword to filter event titles (e.g. `AI`, `crypto`) |
| `SCRAPER_LIMIT`         | `0`                     | Max events to keep per run (`0` = keep all)          |
| `SCRAPER_STRATEGY`      | `web`                   | Scraper backend (`web` is the only current option)   |
| `RETRY_ATTEMPTS`        | `3`                     | How many times to retry on a network failure         |
| `RETRY_BACKOFF_SECONDS` | `5`                     | Seconds to wait between retries (linear backoff)     |
| `API_TOKEN`             | _(none)_                | Reserved for a future API-based scraper strategy     |

**Example — filter to AI events and cap at 20:**

```bash
SCRAPER_SEARCH_TERM=AI SCRAPER_LIMIT=20 DB_PATH=./events.db poetry run garys-events-run-once
```

---

## Docker (One-Shot Container)

The container runs once and exits. Schedule it externally — no cron daemon runs inside the image.

```bash
# Build the image
docker compose build scraper

# Run one scrape pass
docker compose run --rm scraper
```

**Override the DB path or filter at runtime:**

```bash
docker compose run --rm -e DB_PATH=/data/events.db -e SCRAPER_SEARCH_TERM=AI scraper
```

**Schedule with host cron (every day at 8 AM):**

```cron
0 8 * * * cd /path/to/project && docker compose run --rm scraper
```

**Or use the included Kubernetes CronJob manifest:**

```bash
kubectl apply -f deploy/k8s-cronjob.yaml
```

See [docs/RUNBOOK.md](docs/RUNBOOK.md) for full deployment details.

---

## Database Schema

Events are stored in three tables:

- **`runs`** — one row per pipeline execution (timestamp, status, source, attempts)
- **`products`** — deduplicated event records (title + URL = unique key)
- **`product_snapshots`** — links each run to the events captured in that run

This lets you query event history across runs and detect when events appear or disappear.

---

## Error Handling

The package raises typed domain exceptions — no silent failures:

| Exception             | When it's raised                                      |
| --------------------- | ----------------------------------------------------- |
| `ScraperNetworkError` | HTTP error, connection refused, or bad status code    |
| `ScraperTimeoutError` | Request timed out (subclass of `ScraperNetworkError`) |
| `ScraperParseError`   | HTML structure could not be parsed into events        |
| `StorageError`        | SQLite read/write failure                             |

Transient errors (`ScraperNetworkError`) are retried automatically. Non-transient errors propagate immediately.

---

## Architecture

The package is split into focused, single-purpose modules:

| Module                 | Responsibility                                     |
| ---------------------- | -------------------------------------------------- |
| `scraper.py`           | HTTP fetching and HTML parsing of GarysGuide pages |
| `runner_once.py`       | Pipeline orchestration (scrape → filter → persist) |
| `storage.py`           | SQLite persistence (`SQLiteEventStore`)            |
| `filters.py`           | Keyword filtering logic                            |
| `formatters.py`        | JSON serialization for AI/downstream use           |
| `newsletter_parser.py` | Parses newsletter HTML exports as a fallback       |
| `http.py`              | `requests` adapter — the only file that uses HTTP  |
| `protocols.py`         | `typing.Protocol` interfaces for all boundaries    |
| `exceptions.py`        | Domain exception hierarchy                         |
| `models.py`            | `Event` dataclass                                  |
| `config.py`            | Loads configuration from environment variables     |
| `scheduler.py`         | Retry/backoff helpers                              |

---

## Development

```bash
# Install dependencies
poetry install

# Run all tests
poetry run pytest

# Verify the Docker image builds correctly
./scripts/verify_build.sh
```

Tests use injected HTTP doubles — no real network calls, no `requests-mock`. See [docs/TESTING_STRATEGY.md](docs/TESTING_STRATEGY.md).

---

## Docs

- [Runbook](docs/RUNBOOK.md) — deployment, scheduling, operations
- [Testing Strategy](docs/TESTING_STRATEGY.md) — test boundaries and design
- [Requirements Traceability](docs/TRACEABILITY.md) — requirement-to-code mapping
- [Submission Checklist](docs/SUBMISSION_CHECKLIST.md) — project deliverable checklist

---

## License

MIT
