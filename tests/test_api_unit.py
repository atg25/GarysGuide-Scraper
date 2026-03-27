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


def _seed_date_range_events(db_path: str):
    store = SQLiteEventStore(db_path)
    store.init_schema()
    store.persist_run(
        source="web",
        fetched_at="2026-03-26T00:00:00+00:00",
        search_term="",
        record_limit=10,
        status="success",
        attempts=1,
        error="",
        events=[
            {
                "title": "AI Demo Day",
                "url": "https://www.garysguide.com/events/10",
                "description": "AI showcase",
                "price": "FREE",
                "date": "Mar 30",
                "time": "6:00 PM",
                "location": "NYC",
                "tags": ["ai", "demo"],
            },
            {
                "title": "Founder Meetup",
                "url": "https://www.garysguide.com/events/11",
                "description": "General startup meetup",
                "price": "FREE",
                "date": "Apr 01",
                "time": "7:00 PM",
                "location": "NYC",
                "tags": ["startup"],
            },
            {
                "title": "May Investor Night",
                "url": "https://www.garysguide.com/events/12",
                "description": "Funding panel",
                "price": "FREE",
                "date": "May 01",
                "time": "7:00 PM",
                "location": "NYC",
                "tags": ["finance"],
            },
        ],
        today=date(2026, 3, 26),
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
    assert all(
        "ai" in " ".join(event["tags"]).lower() or "ai" in event["title"].lower()
        for event in payload["events"]
    )


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


def test_mcp_list_tools_endpoint_returns_tool_descriptor(tmp_path, monkeypatch):
    db_path = str(tmp_path / "events.db")
    monkeypatch.setenv("DB_PATH", db_path)
    monkeypatch.setenv("API_TOKEN", "secret")
    monkeypatch.setenv("GARYS_EVENTS_MCP_ENABLED", "true")
    get_config.cache_clear()
    _seed_events(db_path)

    client = TestClient(create_app())
    response = client.post(
        "/mcp",
        json={"method": "ListTools", "params": {}},
        headers={"Authorization": "Bearer secret"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "tools" in payload
    assert len(payload["tools"]) == 1
    assert payload["tools"][0]["name"] == "garys_events.query_events"


def test_mcp_call_tool_validation_error_is_returned(tmp_path, monkeypatch):
    db_path = str(tmp_path / "events.db")
    monkeypatch.setenv("DB_PATH", db_path)
    monkeypatch.setenv("API_TOKEN", "secret")
    monkeypatch.setenv("GARYS_EVENTS_MCP_ENABLED", "true")
    get_config.cache_clear()
    _seed_events(db_path)

    client = TestClient(create_app())
    response = client.post(
        "/mcp",
        json={
            "method": "CallTool",
            "params": {
                "name": "garys_events.query_events",
                "arguments": {},
            },
        },
        headers={"Authorization": "Bearer secret"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error"]["code"] == "validation_error"


def test_events_date_range_filter_matches_known_window_ai_false(tmp_path, monkeypatch):
    db_path = str(tmp_path / "events.db")
    monkeypatch.setenv("DB_PATH", db_path)
    monkeypatch.delenv("API_TOKEN", raising=False)
    get_config.cache_clear()
    _seed_date_range_events(db_path)

    client = TestClient(create_app())
    unfiltered = client.get("/events?ai_only=false&limit=10")
    filtered = client.get(
        "/events?ai_only=false&date_from=2026-03-26&date_to=2026-04-01&limit=10"
    )

    assert unfiltered.status_code == 200
    assert filtered.status_code == 200
    unfiltered_titles = {event["title"] for event in unfiltered.json()["events"]}
    filtered_titles = {event["title"] for event in filtered.json()["events"]}
    assert filtered.json()["count"] == 2
    assert filtered_titles.issubset(unfiltered_titles)
    assert "AI Demo Day" in filtered_titles
    assert "Founder Meetup" in filtered_titles
    assert "May Investor Night" not in filtered_titles


def test_events_date_range_filter_matches_known_window_ai_true(tmp_path, monkeypatch):
    db_path = str(tmp_path / "events.db")
    monkeypatch.setenv("DB_PATH", db_path)
    monkeypatch.delenv("API_TOKEN", raising=False)
    get_config.cache_clear()
    _seed_date_range_events(db_path)

    client = TestClient(create_app())
    response = client.get(
        "/events?ai_only=true&date_from=2026-03-26&date_to=2026-04-01&limit=10"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["events"][0]["title"] == "AI Demo Day"
