from __future__ import annotations

import io
import json

from garys_nyc_events.mcp.server import TOOL_NAME, run_stdio_loop


def _run_requests(lines: list[str], enabled: bool = True) -> list[dict]:
    stdin = io.StringIO("\n".join(lines) + "\n")
    stdout = io.StringIO()
    run_stdio_loop(in_stream=stdin, out_stream=stdout, enabled=enabled)
    return [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]


def test_stdio_listtools_and_calltool_end_to_end():
    responses = _run_requests(
        [
            json.dumps({"method": "ListTools"}),
            json.dumps(
                {
                    "method": "CallTool",
                    "params": {"name": TOOL_NAME, "arguments": {"limit": 1}},
                }
            ),
        ],
        enabled=True,
    )

    assert len(responses) == 2
    assert responses[0]["tools"][0]["name"] == TOOL_NAME
    assert responses[1]["ok"] is False
    assert responses[1]["error"]["code"] == "config_error"


def test_stdio_invalid_calltool_payload_is_safe_error():
    responses = _run_requests(
        [
            json.dumps(
                {
                    "method": "CallTool",
                    "params": {"name": TOOL_NAME, "arguments": "bad"},
                }
            )
        ],
        enabled=True,
    )

    assert responses[0]["ok"] is False
    assert responses[0]["error"]["code"] == "invalid_request"
