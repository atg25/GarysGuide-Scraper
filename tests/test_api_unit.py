from datetime import date

from fastapi.testclient import TestClient

from garys_nyc_events.api.app import create_app
from garys_nyc_events.api.dependencies import get_config
from garys_nyc_events.storage import SQLiteEventStore


def _seed_events(db_path: str):
    store = SQLiteEventStore(db_path)
    store.init_schema()
    store.persist_run(
        source="web",
        fetched_at="2026-02-26T00:00:00+00:00",
        search_term="AI",
        record_limit=10,
        status="success",
        attempts=1,
        error="",
        events=[
            {
                "title": "NYC AI Summit",
                "url": "https://www.garysguide.com/events/1",
                "description": "AI builders",
                "price": "FREE",
                "date": "2026-02-27",
                "time": "7:00 PM",
                "location": "NYC",
                "tags": ["ai", "summit"],
            },
            {
                "title": "Cooking Club",
                "url": "https://www.garysguide.com/events/2",
                "description": "food meetup",
                "price": "FREE",
                "date": "2026-02-27",
                "time": "6:00 PM",
                "location": "NYC",
                "tags": ["social"],
            },
        ],
        today=date(2026, 2, 26),
    )


def test_health_returns_200(tmp_path, monkeypatch):
    db_path = str(tmp_path / "events.db")
    monkeypatch.setenv("DB_PATH", db_path)
    get_config.cache_clear()
    _seed_events(db_path)

    client = TestClient(create_app())
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_events_requires_auth_when_api_token_set(tmp_path, monkeypatch):
    db_path = str(tmp_path / "events.db")
    monkeypatch.setenv("DB_PATH", db_path)
    monkeypatch.setenv("API_TOKEN", "secret")
    get_config.cache_clear()
    _seed_events(db_path)

    client = TestClient(create_app())
    response = client.get("/events")

    assert response.status_code == 401


def test_events_valid_token_returns_event_list(tmp_path, monkeypatch):
    db_path = str(tmp_path / "events.db")
    monkeypatch.setenv("DB_PATH", db_path)
    monkeypatch.setenv("API_TOKEN", "secret")
    get_config.cache_clear()
    _seed_events(db_path)

    client = TestClient(create_app())
    response = client.get("/events", headers={"Authorization": "Bearer secret"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    assert "events" in payload


def test_events_ai_only_filter(tmp_path, monkeypatch):
    db_path = str(tmp_path / "events.db")
    monkeypatch.setenv("DB_PATH", db_path)
    monkeypatch.delenv("API_TOKEN", raising=False)
    get_config.cache_clear()
    _seed_events(db_path)

    client = TestClient(create_app())
    response = client.get("/events?ai_only=true")

    assert response.status_code == 200
    payload = response.json()
    assert all("ai" in " ".join(event["tags"]).lower() or "ai" in event["title"].lower() for event in payload["events"])


def test_event_by_id_returns_404_for_missing(tmp_path, monkeypatch):
    db_path = str(tmp_path / "events.db")
    monkeypatch.setenv("DB_PATH", db_path)
    get_config.cache_clear()
    _seed_events(db_path)

    client = TestClient(create_app())
    response = client.get("/events/99999")

    assert response.status_code == 404


def test_trigger_run_requires_api_token_configured(tmp_path, monkeypatch):
    db_path = str(tmp_path / "events.db")
    monkeypatch.setenv("DB_PATH", db_path)
    monkeypatch.delenv("API_TOKEN", raising=False)
    get_config.cache_clear()

    client = TestClient(create_app())
    response = client.post("/runs/trigger")

    assert response.status_code == 503


def test_runs_list_returns_recent_runs(tmp_path, monkeypatch):
    db_path = str(tmp_path / "events.db")
    monkeypatch.setenv("DB_PATH", db_path)
    monkeypatch.setenv("API_TOKEN", "secret")
    get_config.cache_clear()
    _seed_events(db_path)

    client = TestClient(create_app())
    response = client.get("/runs", headers={"Authorization": "Bearer secret"})

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_openapi_json_is_valid(tmp_path, monkeypatch):
    db_path = str(tmp_path / "events.db")
    monkeypatch.setenv("DB_PATH", db_path)
    get_config.cache_clear()

    client = TestClient(create_app())
    response = client.get("/openapi.json")

    assert response.status_code == 200
    payload = response.json()
    assert "paths" in payload
    assert "/events" in payload["paths"]
