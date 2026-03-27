from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from garys_nyc_events.mcp.tools.query_events import query_events


class _Handler(BaseHTTPRequestHandler):
    status_code = 200
    payload = {"count": 1, "events": [{"title": "AI Event"}]}

    def do_GET(self):  # noqa: N802
        if self.path.startswith("/events"):
            body = json.dumps(self.payload).encode("utf-8")
            self.send_response(self.status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, _format, *_args):
        return


def _start_server() -> tuple[HTTPServer, int]:
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


def test_adapter_calls_local_rest_api(monkeypatch):
    _Handler.status_code = 200
    _Handler.payload = {"count": 2, "events": [{"title": "A"}, {"title": "B"}]}

    server, port = _start_server()
    monkeypatch.setenv("GARYS_EVENTS_REST_API_BASE_URL", f"http://127.0.0.1:{port}")

    try:
        result = query_events({"ai_only": True, "limit": 10})
    finally:
        server.shutdown()

    assert result["ok"] is True
    assert result["data"]["count"] == 2


def test_adapter_normalizes_non_2xx(monkeypatch):
    _Handler.status_code = 503
    _Handler.payload = {"detail": "temporary"}

    server, port = _start_server()
    monkeypatch.setenv("GARYS_EVENTS_REST_API_BASE_URL", f"http://127.0.0.1:{port}")

    try:
        result = query_events({"ai_only": True, "limit": 10})
    finally:
        server.shutdown()

    assert result["ok"] is False
    assert result["error"]["code"] == "upstream_transient"
    assert result["error"]["retriable"] is True
