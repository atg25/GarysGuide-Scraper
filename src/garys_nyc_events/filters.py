from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List, Optional

from dateutil import parser as date_parser


AI_KEYWORDS = frozenset(
    {
        "ai",
        "artificial intelligence",
        "machine learning",
        "ml",
        "llm",
        "deep learning",
        "generative ai",
        "gpt",
        "nlp",
        "data science",
        "neural network",
        "robotics",
        "computer vision",
    }
)


def filter_events_by_keyword(
    events: List[Dict[str, str]],
    keyword: str,
) -> List[Dict[str, str]]:
    needle = keyword.lower().strip()
    if not needle:
        return events
    return [event for event in events if needle in event.get("title", "").lower()]


def _parse_event_date(value: str, today: date) -> Optional[date]:
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        parsed = date_parser.parse(
            cleaned, fuzzy=True, default=date_parser.parse(str(today))
        )
    except (ValueError, OverflowError):
        return None
    return parsed.date()


def filter_events_upcoming_week(
    events: List[Dict[str, str]],
    today: Optional[date] = None,
) -> List[Dict[str, str]]:
    anchor = today or date.today()
    end = anchor + timedelta(days=7)
    filtered: List[Dict[str, str]] = []

    for event in events:
        parsed_date = _parse_event_date(event.get("date", ""), anchor)
        if parsed_date is None:
            continue
        if anchor <= parsed_date < end:
            filtered.append(event)
    return filtered


def filter_ai_events(events: List[Dict[str, str]]) -> List[Dict[str, str]]:
    filtered: List[Dict[str, str]] = []
    for event in events:
        title = event.get("title", "").lower()
        description = event.get("description", "").lower()
        haystack = f"{title} {description}"
        if any(keyword in haystack for keyword in AI_KEYWORDS):
            filtered.append(event)
    return filtered
