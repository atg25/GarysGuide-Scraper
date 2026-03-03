# garys_nyc_events

A Python package that scrapes NYC tech events from [GarysGuide](https://www.garysguide.com/events), tags them with AI, persists them to SQLite, and exposes them through a REST API — all configurable via environment variables.

---

## What This Tool Does

- **Scrapes** the GarysGuide NYC events page and extracts structured event data
- **Tags events with AI** using Gemini, adding 3–7 descriptive labels per event (e.g. `["ai", "workshop", "free"]`)
- **Filters** events by keyword (e.g. `AI`, `Python`, `startup`)
- **Deduplicates** events across runs so repeat scrapes don't create duplicates
- **Persists** every run and all events to a local SQLite database with full history
- **Serves a REST API** (FastAPI) to query events, inspect run history, and trigger new scrapes
- **Parses newsletter HTML** as a fallback data source when live scraping is unavailable
- **Retries automatically** on transient network errors with configurable backoff
- **Runs as a one-shot container** or a **long-running cron scheduler** — your choice

---

## Install

```bash
pip install garys_nyc_events
```

For local development with [Poetry](https://python-poetry.org/):

```bash
poetry install
```

---

## Quick Start

### Run the full pipeline once (scrape → tag → persist)

```bash
DB_PATH=./garys_events.db poetry run garys-events-run-once
```

This scrapes GarysGuide, tags events with Gemini (if `GEMINI_API_KEY` is set), applies any keyword filter, and saves everything to `garys_events.db`.

Verify the database afterwards:

```bash
DB_PATH=./garys_events.db ./scripts/verify_db.sh
```

### Start the REST API

```bash
DB_PATH=./garys_events.db API_TOKEN=secret poetry run uvicorn garys_nyc_events.api.app:app
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

---

## Python Library Usage

### Scrape events

```python
from garys_nyc_events import scrape_default_garys_guide

# One-liner — returns a list of event dicts
events = scrape_default_garys_guide(delay_seconds=1.5)

# More control with the class
from garys_nyc_events import GarysGuideScraper

scraper = GarysGuideScraper(delay_seconds=1.0, timeout_seconds=10)
events = scraper.get_events()
```

### Filter events by keyword

```python
from garys_nyc_events import filter_events_by_keyword

ai_events = filter_events_by_keyword(events, "AI")
# Case-insensitive title match
```

### Export filtered events as JSON

```python
from garys_nyc_events import get_events_ai_json

json_str = get_events_ai_json(events, keyword="AI")
print(json_str)  # Pretty-printed JSON array
```

### Parse a newsletter HTML export (fallback)

If you have a GarysGuide newsletter saved as HTML from your email client, you can extract events without any network calls:

```python
from garys_nyc_events import parse_newsletter_html

with open("newsletter.html") as f:
    raw_html = f.read()

events = parse_newsletter_html(raw_html)
# Events have source="newsletter_fallback"
# Unsubscribe, social, and sponsor links are skipped automatically
```

---

## Event Schema

Each event stored in the database and returned by the API contains:

| Field         | Example                                   |
| ------------- | ----------------------------------------- |
| `id`          | `42`                                      |
| `title`       | `"AI Demo Night at Cornell Tech"`         |
| `date`        | `"Wed, Mar 5"`                            |
| `time`        | `"7:00 PM"`                               |
| `location`    | `"Cornell Tech, Roosevelt Island"`        |
| `description` | `"Join us for demos from AI startups..."` |
| `price`       | `"FREE"` or `"$25"`                       |
| `url`         | `"https://www.garysguide.com/events/..."` |
| `date_found`  | `"2026-03-03"`                            |
| `tags`        | `["ai", "demo", "free", "networking"]`    |

---

## REST API

The API is built with FastAPI. Start it with `uvicorn garys_nyc_events.api.app:app` or via Docker (see below).

### Authentication

Set `API_TOKEN` in your environment. All endpoints require a Bearer token:

```
Authorization: Bearer <your-token>
```

If `API_TOKEN` is not set, read endpoints are open. The `POST /runs/trigger` endpoint always requires a token.

### Endpoints

| Method | Path            | Description                                      |
| ------ | --------------- | ------------------------------------------------ |
| `GET`  | `/health`       | Health check — returns status and DB event count |
| `GET`  | `/events`       | List events with optional filters                |
| `GET`  | `/events/{id}`  | Get a single event by ID                         |
| `GET`  | `/runs`         | Get the most recent scrape run                   |
| `POST` | `/runs/trigger` | Trigger a new scrape run immediately             |

### `GET /events` query parameters

| Parameter   | Default  | Description                                       |
| ----------- | -------- | ------------------------------------------------- |
| `ai_only`   | `true`   | Return only AI-tagged events                      |
| `limit`     | `100`    | Maximum number of events to return (`0` = all)    |
| `tags`      | `""`     | Comma-separated tag filter (e.g. `workshop,free`) |
| `date_from` | _(none)_ | Start of date window (`YYYY-MM-DD`)               |
| `date_to`   | _(none)_ | End of date window (`YYYY-MM-DD`)                 |

**Example:**

```bash
curl -H "Authorization: Bearer secret" \
  "http://localhost:8000/events?ai_only=true&tags=workshop,free&limit=10"
```

---

## Configuration

All settings are environment variables. No config files needed.

| Variable                    | Default             | Description                                                            |
| --------------------------- | ------------------- | ---------------------------------------------------------------------- |
| `DB_PATH`                   | `./garys_events.db` | Path to the SQLite database file                                       |
| `SCRAPER_SEARCH_TERM`       | _(none)_            | Keyword to filter event titles (e.g. `AI`, `crypto`)                   |
| `SCRAPER_LIMIT`             | `0`                 | Max events to keep per run (`0` = keep all)                            |
| `SCRAPER_STRATEGY`          | `web`               | Scraper backend (`web` is the only current option)                     |
| `SCRAPER_DEDUP_WINDOW_DAYS` | `0`                 | Skip events already seen within this many days (`0` = no dedup window) |
| `RETRY_ATTEMPTS`            | `3`                 | How many times to retry on a network failure                           |
| `RETRY_BACKOFF_SECONDS`     | `5`                 | Seconds to wait between retries                                        |
| `GEMINI_API_KEY`            | _(none)_            | Gemini API key for AI tagging (tagging skipped if unset)               |
| `TAGGING_ENABLED`           | `true`              | Set to `false` to disable AI tagging entirely                          |
| `API_TOKEN`                 | _(none)_            | Bearer token to protect the REST API                                   |
| `CRON_SCHEDULE`             | `0 8 * * *`         | Cron expression for the scheduler service                              |

**Example — filter to AI events, cap at 20, tag with Gemini:**

```bash
SCRAPER_SEARCH_TERM=AI \
SCRAPER_LIMIT=20 \
GEMINI_API_KEY=your-key \
DB_PATH=./garys_events.db \
poetry run garys-events-run-once
```

---

## Docker

The project includes two Docker services in `docker-compose.yml`:

| Service     | Behavior                                                         |
| ----------- | ---------------------------------------------------------------- |
| `scraper`   | Runs once and exits — use with external cron or `run --rm`       |
| `scheduler` | Long-running container that fires the scraper on a cron schedule |

### One-shot scrape

```bash
# Build
docker compose build scraper

# Run once
docker compose run --rm scraper

# Override settings at runtime
docker compose run --rm -e SCRAPER_SEARCH_TERM=AI -e GEMINI_API_KEY=your-key scraper
```

### Cron scheduler (runs automatically)

```bash
# Start the scheduler (runs daily at 8 AM by default)
docker compose up -d scheduler

# Change the schedule via .env
echo "CRON_SCHEDULE=0 6 * * *" >> .env

# View scheduler logs
docker compose logs -f scheduler
```

### Kubernetes CronJob

```bash
kubectl apply -f deploy/k8s-cronjob.yaml
```

See [docs/RUNBOOK.md](docs/RUNBOOK.md) for full deployment details.

---

## Database Schema

Events are stored in three tables:

| Table           | Contents                                                     |
| --------------- | ------------------------------------------------------------ |
| `runs`          | One row per pipeline execution (timestamp, status, attempts) |
| `all events`    | Deduplicated event records across all scrapes                |
| `weekly_events` | View of events in the upcoming 7-day window                  |

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

| Module                 | Responsibility                                           |
| ---------------------- | -------------------------------------------------------- |
| `scraper.py`           | HTTP fetching and HTML parsing of GarysGuide pages       |
| `runner_once.py`       | Pipeline orchestration (scrape → tag → filter → persist) |
| `tagger.py`            | Gemini AI tagging (`GeminiTagger`)                       |
| `storage.py`           | SQLite persistence (`SQLiteEventStore`)                  |
| `filters.py`           | Keyword and date-window filtering                        |
| `formatters.py`        | JSON serialization for downstream use                    |
| `newsletter_parser.py` | Parses newsletter HTML exports as a fallback             |
| `http.py`              | `requests` adapter — the only module that hits HTTP      |
| `protocols.py`         | `typing.Protocol` interfaces for all boundaries          |
| `exceptions.py`        | Domain exception hierarchy                               |
| `models.py`            | `Event` dataclass                                        |
| `config.py`            | Loads `PipelineConfig` from environment variables        |
| `scheduler.py`         | Retry/backoff helpers                                    |
| `api/`                 | FastAPI application, routers, auth, and schemas          |

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
