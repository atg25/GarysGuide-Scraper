from __future__ import annotations

import json
from typing import Dict, List

from .filters import filter_events_by_keyword


def get_events_ai_json(events: List[Dict[str, str]], keyword: str = "AI") -> str:
    ai_events = filter_events_by_keyword(events, keyword)
    return json.dumps(ai_events, ensure_ascii=False, indent=2)
