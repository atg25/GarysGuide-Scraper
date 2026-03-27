from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Optional

import requests


logger = logging.getLogger("garys_nyc_events.tagger")

GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent"
)

TAG_PROMPT_TEMPLATE = """
You are a concise event tagger. Given the event metadata below, respond with ONLY a
JSON array of 3-7 lowercase short tags that best classify this event.
Do NOT include any explanation, markdown, or extra text.

Title: {title}
Description: {description}
Location: {location}

Example output: ["ai", "workshop", "free", "networking", "llm"]
"""


class GeminiTagger:
    def __init__(
        self,
        api_key: Optional[str] = None,
        session: Optional[requests.Session] = None,
        max_tags: int = 7,
    ) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.session = session or requests.Session()
        self.max_tags = max_tags

    def is_available(self) -> bool:
        return bool(self.api_key)

    def tag_event(self, event: Dict[str, str]) -> List[str]:
        if not self.is_available():
            return []

        prompt = TAG_PROMPT_TEMPLATE.format(
            title=event.get("title", ""),
            description=event.get("description", "")[:500],
            location=event.get("location", ""),
        )
        try:
            return self._call_gemini(prompt)
        except Exception as exc:
            logger.warning("Gemini tagging failed for %r: %s", event.get("title"), exc)
            return []

    def tag_events(self, events: List[Dict[str, str]]) -> List[Dict[str, str]]:
        return [{**event, "tags": self.tag_event(event)} for event in events]

    def _call_gemini(self, prompt: str) -> List[str]:
        if not self.api_key:
            return []

        response = self.session.post(
            f"{GEMINI_ENDPOINT}?key={self.api_key}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        text = payload["candidates"][0]["content"]["parts"][0]["text"]

        parsed = json.loads(text)
        if not isinstance(parsed, list):
            raise ValueError("Gemini response is not a JSON list")

        tags = [str(item).strip().lower() for item in parsed if str(item).strip()]
        return tags[: self.max_tags]
