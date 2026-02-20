from __future__ import annotations

from typing import Dict, List


def filter_events_by_keyword(
    events: List[Dict[str, str]],
    keyword: str,
) -> List[Dict[str, str]]:
    needle = keyword.lower().strip()
    if not needle:
        return events
    return [event for event in events if needle in event.get("title", "").lower()]
