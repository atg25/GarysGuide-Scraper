from __future__ import annotations

import os
import re
from datetime import date
from typing import Any, Mapping

import requests


def _error(code: str, message: str, *, retriable: bool) -> dict[str, Any]:
    return {
        "ok": False,
        "error": {"code": code, "message": message, "retriable": retriable},
    }


def _timeout_seconds() -> float:
    raw = os.getenv("GARYS_EVENTS_REST_API_TIMEOUT_MS", "10000").strip()
    try:
        timeout_ms = int(raw)
    except ValueError:
        timeout_ms = 10000
    if timeout_ms <= 0:
        timeout_ms = 10000
    return timeout_ms / 1000.0


def _base_url() -> str:
    return os.getenv("GARYS_EVENTS_REST_API_BASE_URL", "").strip().rstrip("/")


def _validation_error(message: str) -> dict[str, Any]:
    return _error("validation_error", message, retriable=False)


def _validate_arguments(
    arguments: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    allowed = {"ai_only", "limit", "tags", "date_from", "date_to"}
    unknown = set(arguments.keys()) - allowed
    if unknown:
        return None, _validation_error(f"Unknown fields: {', '.join(sorted(unknown))}")

    if "limit" not in arguments:
        return None, _validation_error("Missing required field: limit")

    limit = arguments.get("limit")
    if not isinstance(limit, int) or not (0 <= limit <= 500):
        return None, _validation_error("limit must be an integer between 0 and 500")

    ai_only = arguments.get("ai_only", True)
    if not isinstance(ai_only, bool):
        return None, _validation_error("ai_only must be a boolean")

    tags: list[str] = []
    raw_tags = arguments.get("tags", [])
    if raw_tags is not None:
        if not isinstance(raw_tags, list):
            return None, _validation_error("tags must be an array of strings")
        if len(raw_tags) > 50:
            return None, _validation_error("tags cannot contain more than 50 values")
        for token in raw_tags:
            if not isinstance(token, str):
                return None, _validation_error("tags must be an array of strings")
            if len(token) > 64:
                return None, _validation_error("tag value is too long")
            cleaned = token.strip().lower()
            if cleaned:
                tags.append(cleaned)

    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    date_from = arguments.get("date_from")
    date_to = arguments.get("date_to")
    parsed_from: date | None = None
    parsed_to: date | None = None

    if date_from is not None:
        if not isinstance(date_from, str) or not date_pattern.match(date_from):
            return None, _validation_error("date_from must match YYYY-MM-DD")
        try:
            parsed_from = date.fromisoformat(date_from)
        except ValueError:
            return None, _validation_error("date_from must be a valid calendar date")

    if date_to is not None:
        if not isinstance(date_to, str) or not date_pattern.match(date_to):
            return None, _validation_error("date_to must match YYYY-MM-DD")
        try:
            parsed_to = date.fromisoformat(date_to)
        except ValueError:
            return None, _validation_error("date_to must be a valid calendar date")

    if parsed_from and parsed_to and parsed_from > parsed_to:
        return None, _validation_error("date_from cannot be later than date_to")

    normalized: dict[str, Any] = {
        "ai_only": ai_only,
        "limit": limit,
    }
    if tags:
        normalized["tags"] = tags
    if date_from is not None:
        normalized["date_from"] = date_from
    if date_to is not None:
        normalized["date_to"] = date_to

    return normalized, None


def _build_params(arguments: Mapping[str, Any]) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if "ai_only" in arguments:
        params["ai_only"] = arguments.get("ai_only")
    if "limit" in arguments:
        params["limit"] = arguments.get("limit")
    if "date_from" in arguments:
        params["date_from"] = arguments.get("date_from")
    if "date_to" in arguments:
        params["date_to"] = arguments.get("date_to")

    tags = arguments.get("tags")
    if isinstance(tags, list) and tags:
        params["tags"] = ",".join(str(tag) for tag in tags)

    return params


def _normalized_from_response(response: requests.Response) -> dict[str, Any]:
    if response.status_code in {429, 503, 504}:
        return _error(
            "upstream_transient", "Temporary upstream failure", retriable=True
        )

    if 400 <= response.status_code < 500:
        return _error(
            "upstream_client_error", "Upstream request rejected", retriable=False
        )

    if response.status_code >= 500:
        return _error(
            "upstream_server_error", "Upstream service error", retriable=False
        )

    try:
        payload = response.json()
    except ValueError:
        return _error(
            "upstream_parse_error",
            "Upstream response was not valid JSON",
            retriable=False,
        )

    if not isinstance(payload, Mapping):
        return _error(
            "upstream_parse_error",
            "Upstream response shape is invalid",
            retriable=False,
        )

    events = payload.get("events", [])
    count = payload.get("count", 0)
    if not isinstance(events, list):
        return _error(
            "upstream_parse_error", "Upstream events shape is invalid", retriable=False
        )
    if not isinstance(count, int):
        count = len(events)

    return {"ok": True, "data": {"count": count, "events": events}}


def query_events(_arguments: Mapping[str, Any]) -> dict[str, Any]:
    normalized_args, validation_error = _validate_arguments(_arguments)
    if validation_error is not None:
        return validation_error

    base_url = _base_url()
    if not base_url:
        return _error("config_error", "Missing REST API base URL", retriable=False)

    try:
        response = requests.get(
            f"{base_url}/events",
            params=_build_params(normalized_args or {}),
            timeout=_timeout_seconds(),
        )
    except requests.Timeout:
        return _error("upstream_timeout", "Upstream request timed out", retriable=True)
    except requests.ConnectionError:
        return _error(
            "upstream_network_error", "Upstream network failure", retriable=True
        )
    except requests.RequestException:
        return _error(
            "upstream_request_error", "Upstream request failed", retriable=False
        )

    return _normalized_from_response(response)
