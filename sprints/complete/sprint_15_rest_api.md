# Sprint 15 — Public REST API: NYC AI Events as a Service

**Status:** Planned
**Addresses:** Goal 4 — Make the tool an API that anyone can use

---

## Goal

Expose the Gary's Guide NYC AI event database as a public **FastAPI** REST API so that any HTTP
client can query upcoming AI events, filter by date/tag, and trigger manual scrape runs — all
without needing Python or local tooling. Ship with a live OpenAPI/Swagger UI and a Docker
entrypoint that starts both the scraper scheduler and the API server in a single container.

---

## Rationale

The scraper currently produces data that lives in a local SQLite file accessible only to the
process that runs it. Neither a colleague, a mobile app, nor an external integration can consume
it. A REST layer with JSON responses, standard auth, and a Swagger UI turns this personal script
into a first-class, shareable service.

**Why FastAPI?**
- Native OpenAPI + Swagger UI at `/docs` with zero extra configuration.
- `Annotated` dependency injection makes auth and DB injection straightforward.
- `httpx.AsyncClient` + `fastapi.testclient.TestClient` make all three test tiers trivial.

---

## Tasks

### 1. Create `src/garys_nyc_events/api/` package

```
src/garys_nyc_events/api/
    __init__.py
    app.py          # FastAPI application factory
    auth.py         # Bearer token dependency
    dependencies.py # DB store dependency
    routers/
        __init__.py
        events.py   # /events endpoints
        runs.py     # /runs endpoints
        health.py   # /health
    schemas.py      # Pydantic I/O models
```

---

### 2. Define Pydantic response schemas (`schemas.py`)

```python
class EventOut(BaseModel):
    title: str
    date: str
    time: str
    location: str
    description: str
    price: str
    url: str
    source: str
    tags: List[str]

class EventListOut(BaseModel):
    count: int
    events: List[EventOut]

class Runout(BaseModel):
    run_id: int
    status: str
    source: str
    attempts: int
    fetched_count: int
    error: str

class TriggerRunOut(BaseModel):
    message: str
    run: RunOut
```

---

### 3. Implement API endpoints (`routers/events.py`, `routers/runs.py`, `routers/health.py`)

#### `/health` (public, no auth)
- `GET /health` → `{"status": "ok", "db_event_count": <int>}`

#### `/events` (requires Bearer token)
- `GET /events` — query params: `ai_only: bool = True`, `limit: int = 100`,
  `tags: str = ""` (comma-separated tag filter), `date_from: date = today`,
  `date_to: date = today+7`. Returns `EventListOut`.
- `GET /events/{event_id}` — returns single `EventOut` or `404`.

#### `/runs` (requires Bearer token)
- `GET /runs` — returns list of the last 20 `RunOut` records.
- `POST /runs/trigger` — manually triggers `run_once()` in a background thread; returns
  `TriggerRunOut`. Rate-limited to 1 call per minute per token.

---

### 4. Bearer token auth (`auth.py`)

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status

security = HTTPBearer()

def require_api_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    config: PipelineConfig = Depends(get_config),
) -> None:
    if not config.api_token:
        raise HTTPException(status_code=503, detail="API auth not configured")
    if credentials.credentials != config.api_token:
        raise HTTPException(status_code=401, detail="Invalid API token")
```

`API_TOKEN` env var is already in `PipelineConfig`. If `API_TOKEN` is not set the server starts
in read-only **open mode** and all mutation endpoints (`POST /runs/trigger`) are disabled.

---

### 5. Application factory (`app.py`)

```python
def create_app(config: Optional[PipelineConfig] = None) -> FastAPI:
    cfg = config or load_config_from_env()
    app = FastAPI(
        title="Gary's NYC AI Events API",
        version="1.0.0",
        description="Upcoming NYC AI events scraped from Gary's Guide.",
    )
    app.include_router(health_router)
    app.include_router(events_router, prefix="/events")
    app.include_router(runs_router, prefix="/runs")
    return app
```

---

### 6. Update `Dockerfile` and `docker-compose.yml`

- Add `uvicorn` startup to `run_once_entrypoint.sh` (or a new `entrypoint_api.sh`):
  ```bash
  uvicorn garys_nyc_events.api.app:app --host 0.0.0.0 --port 8000
  ```
- Expose port `8000` in `Dockerfile`.
- Add `api` service to `docker-compose.yml` that mounts the same `/data` volume as the scheduler.

### 7. Add `pyproject.toml` dependencies

```toml
[tool.poetry.dependencies]
fastapi = ">=0.110.0"
uvicorn = {extras = ["standard"], version = ">=0.28.0"}
pydantic = ">=2.0"
httpx = ">=0.27"   # for TestClient + async
```

Add `garys-events-api = "garys_nyc_events.api.app:app"` to `[tool.poetry.scripts]` for local dev.

---

## Acceptance Criteria

- [ ] `GET /health` returns `200` with `{"status": "ok"}` — no auth required.
- [ ] `GET /events` without a valid `Authorization: Bearer <token>` returns `401`.
- [ ] `GET /events` with a valid token returns a JSON body matching `EventListOut`.
- [ ] `GET /events?ai_only=true` returns only events with AI-related tags or titles.
- [ ] `GET /events?date_from=2026-03-01&date_to=2026-03-07` returns only events in that window.
- [ ] `POST /runs/trigger` creates a new run record and returns `202` with `TriggerRunOut`.
- [ ] `POST /runs/trigger` with no `API_TOKEN` configured returns `503`.
- [ ] OpenAPI JSON reachable at `/openapi.json`; Swagger UI at `/docs`.
- [ ] Docker compose `up` starts API on port `8000` with SQLite volume shared with scraper.

---

## Tests Required

### Unit tests — `tests/test_api_unit.py` (new file)

Uses `fastapi.testclient.TestClient` with in-memory SQLite stub store (no real network, no real DB).

| # | Name | Pass/Fail | What it asserts |
|---|------|-----------|-----------------|
| U1 | `test_health_returns_200` | Positive | `GET /health` → `200`, body has `"status": "ok"` |
| U2 | `test_health_no_auth_required` | Positive | `GET /health` without token → `200` (not `401`) |
| U3 | `test_events_requires_auth` | Negative | `GET /events` without token → `403` or `401` |
| U4 | `test_events_invalid_token_rejected` | Negative | `Authorization: Bearer wrong` → `401` |
| U5 | `test_events_valid_token_returns_event_list` | Positive | Seed 3 events → `GET /events` → `count == 3`, first result has all `EventOut` fields |
| U6 | `test_events_ai_only_filter` | Positive | Seed 2 AI + 1 cooking event → `?ai_only=true` → `count == 2` |
| U7 | `test_events_date_range_filter` | Positive | Seed events across 2 weeks → `?date_from&date_to` → correct subset returned |
| U8 | `test_events_tag_filter` | Positive | Seed events with varying tags → `?tags=workshop` → only workshop events |
| U9 | `test_event_by_id_returns_404_for_missing` | Negative | `GET /events/99999` → `404` |
| U10 | `test_trigger_run_requires_api_token_configured` | Negative | `API_TOKEN` unset → `POST /runs/trigger` → `503` |
| U11 | `test_trigger_run_with_valid_token_returns_202` | Positive | `API_TOKEN` set, valid token → `POST /runs/trigger` → `202`, body has `run_id` |
| U12 | `test_runs_list_returns_recent_runs` | Positive | After 3 runs → `GET /runs` → list of 3 run objects |

### Integration tests — `tests/test_api_integration.py` (new file)

Uses `TestClient` with a **real SQLite temp DB** and stub HTTP scraper.

| # | Name | Pass/Fail | What it asserts |
|---|------|-----------|-----------------|
| I1 | `test_full_pipeline_events_visible_via_api` | Positive | `run_once()` with stub scraper → events in DB → `GET /events` returns them |
| I2 | `test_trigger_run_persists_new_events` | Positive | `POST /runs/trigger` → `GET /events` count increases |
| I3 | `test_dedup_across_two_api_triggered_runs` | Positive | Trigger same events twice → `GET /events` count does not double |
| I4 | `test_events_include_gemini_tags` | Positive | Events seeded with tags → API response includes non-empty `tags` list |

### E2E tests — `tests/test_e2e_api.py` (new file, `@pytest.mark.e2e`)

Starts full uvicorn server in-process against live SQLite and live scraper.

| # | Name | Pass/Fail | What it asserts |
|---|------|-----------|-----------------|
| E1 | `test_live_health_endpoint` | Positive | `GET /health` → `200`, `db_event_count >= 0` |
| E2 | `test_live_events_endpoint_returns_ai_events` | Positive | After live scrape → `GET /events?ai_only=true` → all events have AI-relevant title or tag |
| E3 | `test_live_trigger_then_fetch` | Positive | `POST /runs/trigger` → wait → `GET /events` → `count >= 1` |
| E4 | `test_live_invalid_token_blocked` | Negative | Wrong token → `401` on `/events` |
| E5 | `test_live_openapi_json_is_valid` | Positive | `GET /openapi.json` → valid JSON with `"paths"` key containing `/events` |

---

## Definition of Done

- All 21 tests pass at their respective tiers (E2E with `pytest -m e2e`).
- `fastapi`, `uvicorn[standard]`, `httpx`, and `pydantic>=2` added to `pyproject.toml`.
- `docker compose up` starts the API; `curl http://localhost:8000/health` returns `200`.
- `/docs` Swagger UI loads and lists all routes with example schemas.
- `API_TOKEN` env var documented in `README.md` "Running the API" section.
- No regressions in Sprints 1–14 tests.
