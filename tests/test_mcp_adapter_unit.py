from __future__ import annotations

import requests

from garys_nyc_events.mcp.tools.query_events import query_events


class _FakeResponse:
    def __init__(self, status_code: int, payload=None, json_error: bool = False):
        self.status_code = status_code
        self._payload = payload
        self._json_error = json_error

    def json(self):
        if self._json_error:
            raise ValueError("bad json")
        return self._payload


def test_query_events_missing_base_url_returns_config_error(monkeypatch):
    monkeypatch.delenv("GARYS_EVENTS_REST_API_BASE_URL", raising=False)

    result = query_events({"limit": 10})

    assert result["ok"] is False
    assert result["error"]["code"] == "config_error"
    assert result["error"]["retriable"] is False


def test_query_events_timeout_is_retriable(monkeypatch):
    monkeypatch.setenv("GARYS_EVENTS_REST_API_BASE_URL", "http://example.com")

    def _raise(*_args, **_kwargs):
        raise requests.Timeout("timeout")

    monkeypatch.setattr(requests, "get", _raise)

    result = query_events({"limit": 10})

    assert result["ok"] is False
    assert result["error"]["code"] == "upstream_timeout"
    assert result["error"]["retriable"] is True


def test_query_events_connection_error_is_retriable(monkeypatch):
    monkeypatch.setenv("GARYS_EVENTS_REST_API_BASE_URL", "http://example.com")

    def _raise(*_args, **_kwargs):
        raise requests.ConnectionError("network")

    monkeypatch.setattr(requests, "get", _raise)

    result = query_events({"limit": 10})

    assert result["ok"] is False
    assert result["error"]["code"] == "upstream_network_error"
    assert result["error"]["retriable"] is True


def test_query_events_429_is_retriable(monkeypatch):
    monkeypatch.setenv("GARYS_EVENTS_REST_API_BASE_URL", "http://example.com")
    monkeypatch.setattr(
        requests,
        "get",
        lambda *_args, **_kwargs: _FakeResponse(429, {"detail": "rate"}),
    )

    result = query_events({"limit": 10})

    assert result["ok"] is False
    assert result["error"]["code"] == "upstream_transient"
    assert result["error"]["retriable"] is True


def test_query_events_503_is_retriable(monkeypatch):
    monkeypatch.setenv("GARYS_EVENTS_REST_API_BASE_URL", "http://example.com")
    monkeypatch.setattr(
        requests,
        "get",
        lambda *_args, **_kwargs: _FakeResponse(503, {"detail": "down"}),
    )

    result = query_events({"limit": 10})

    assert result["ok"] is False
    assert result["error"]["code"] == "upstream_transient"
    assert result["error"]["retriable"] is True


def test_query_events_400_is_not_retriable(monkeypatch):
    monkeypatch.setenv("GARYS_EVENTS_REST_API_BASE_URL", "http://example.com")
    monkeypatch.setattr(
        requests, "get", lambda *_args, **_kwargs: _FakeResponse(400, {"detail": "bad"})
    )

    result = query_events({"limit": 10})

    assert result["ok"] is False
    assert result["error"]["code"] == "upstream_client_error"
    assert result["error"]["retriable"] is False


def test_query_events_non_json_is_not_retriable(monkeypatch):
    monkeypatch.setenv("GARYS_EVENTS_REST_API_BASE_URL", "http://example.com")
    monkeypatch.setattr(
        requests,
        "get",
        lambda *_args, **_kwargs: _FakeResponse(200, None, json_error=True),
    )

    result = query_events({"limit": 10})

    assert result["ok"] is False
    assert result["error"]["code"] == "upstream_parse_error"
    assert result["error"]["retriable"] is False


def test_query_events_success_normalizes_payload(monkeypatch):
    monkeypatch.setenv("GARYS_EVENTS_REST_API_BASE_URL", "http://example.com")
    monkeypatch.setattr(
        requests,
        "get",
        lambda *_args, **_kwargs: _FakeResponse(
            200, {"count": 1, "events": [{"title": "AI"}]}
        ),
    )

    result = query_events({"limit": 10, "tags": ["ai", "ml"]})

    assert result["ok"] is True
    assert result["data"]["count"] == 1
    assert isinstance(result["data"]["events"], list)
