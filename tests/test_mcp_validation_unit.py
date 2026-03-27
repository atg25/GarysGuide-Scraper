from __future__ import annotations

import requests

from garys_nyc_events.mcp.tools.query_events import query_events


def test_validation_rejects_unknown_fields(monkeypatch):
    monkeypatch.setenv("GARYS_EVENTS_REST_API_BASE_URL", "http://example.com")

    result = query_events({"limit": 10, "unknown": True})

    assert result["ok"] is False
    assert result["error"]["code"] == "validation_error"


def test_validation_rejects_missing_limit(monkeypatch):
    monkeypatch.setenv("GARYS_EVENTS_REST_API_BASE_URL", "http://example.com")

    result = query_events({"ai_only": True})

    assert result["ok"] is False
    assert result["error"]["code"] == "validation_error"


def test_validation_rejects_invalid_limit(monkeypatch):
    monkeypatch.setenv("GARYS_EVENTS_REST_API_BASE_URL", "http://example.com")

    result = query_events({"limit": 999})

    assert result["ok"] is False
    assert result["error"]["code"] == "validation_error"


def test_validation_rejects_invalid_date_format(monkeypatch):
    monkeypatch.setenv("GARYS_EVENTS_REST_API_BASE_URL", "http://example.com")

    result = query_events({"limit": 10, "date_from": "2026/01/01"})

    assert result["ok"] is False
    assert result["error"]["code"] == "validation_error"


def test_validation_rejects_date_range_inversion(monkeypatch):
    monkeypatch.setenv("GARYS_EVENTS_REST_API_BASE_URL", "http://example.com")

    result = query_events(
        {"limit": 10, "date_from": "2026-02-10", "date_to": "2026-02-01"}
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "validation_error"


def test_validation_blocks_adapter_call_on_invalid_payload(monkeypatch):
    monkeypatch.setenv("GARYS_EVENTS_REST_API_BASE_URL", "http://example.com")

    called = {"value": False}

    def _fake_get(*_args, **_kwargs):
        called["value"] = True
        raise AssertionError("adapter should not be called")

    monkeypatch.setattr(requests, "get", _fake_get)

    result = query_events({"limit": -1})

    assert result["ok"] is False
    assert result["error"]["code"] == "validation_error"
    assert called["value"] is False
