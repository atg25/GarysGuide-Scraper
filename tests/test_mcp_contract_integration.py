from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from garys_nyc_events.api.app import create_app
from garys_nyc_events.api.dependencies import get_config
from garys_nyc_events.storage import SQLiteEventStore


_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "mcp_contract"


def _seed_events(db_path: str) -> None:
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
            }
        ],
        today=date(2026, 2, 26),
    )


def _read_fixture(name: str) -> dict:
    return json.loads((_FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_health_response_contract_is_stable(tmp_path, monkeypatch):
    db_path = str(tmp_path / "events.db")
    monkeypatch.setenv("DB_PATH", db_path)
    get_config.cache_clear()
    _seed_events(db_path)

    client = TestClient(create_app())
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"status", "db_event_count"}
    assert payload["status"] == "ok"
    assert isinstance(payload["db_event_count"], int)


def test_events_response_contract_is_stable(tmp_path, monkeypatch):
    db_path = str(tmp_path / "events.db")
    monkeypatch.setenv("DB_PATH", db_path)
    monkeypatch.delenv("API_TOKEN", raising=False)
    get_config.cache_clear()
    _seed_events(db_path)

    client = TestClient(create_app())
    response = client.get("/events?ai_only=true&limit=10")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"count", "events"}
    assert isinstance(payload["count"], int)
    assert isinstance(payload["events"], list)
    assert payload["events"], "expected at least one seeded event"

    event = payload["events"][0]
    expected_keys = {
        "id",
        "title",
        "date",
        "time",
        "location",
        "description",
        "date_found",
        "price",
        "url",
        "tags",
    }
    assert set(event.keys()) == expected_keys


def test_runs_response_contract_is_stable(tmp_path, monkeypatch):
    db_path = str(tmp_path / "events.db")
    monkeypatch.setenv("DB_PATH", db_path)
    monkeypatch.setenv("API_TOKEN", "secret")
    get_config.cache_clear()
    _seed_events(db_path)

    client = TestClient(create_app())
    response = client.get("/runs", headers={"Authorization": "Bearer secret"})

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload, "expected at least one run"
    assert set(payload[0].keys()) == {
        "run_id",
        "status",
        "source",
        "attempts",
        "fetched_count",
        "error",
    }


def test_contract_fixtures_are_valid_and_frozen():
    minimal = _read_fixture("query_events_input_minimal.json")
    assert minimal["ai_only"] is True
    assert isinstance(minimal["limit"], int)
    assert 0 <= minimal["limit"] <= 500

    success = _read_fixture("query_events_success.json")
    assert success["ok"] is True
    assert set(success.keys()) == {"ok", "data"}
    assert set(success["data"].keys()) == {"count", "events"}
    assert isinstance(success["data"]["events"], list)

    failure = _read_fixture("query_events_failure.json")
    assert failure["ok"] is False
    assert set(failure.keys()) == {"ok", "error"}
    assert set(failure["error"].keys()) == {"code", "message", "retriable"}
