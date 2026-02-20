from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List

from bs4 import BeautifulSoup

from .models import Event


def parse_newsletter_html(raw_html: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(raw_html, "html.parser")
    events: List[Event] = []

    ignore_tokens = [
        "unsubscribe",
        "view in browser",
        "privacy",
        "sponsor",
        "advertise",
        "mailto:",
        "facebook.com",
        "twitter.com",
        "linkedin.com",
    ]

    for link in soup.find_all("a", href=True):
        title = link.get_text(strip=True)
        url = link.get("href", "").strip()
        if not title or not url:
            continue
        if any(token in url.lower() for token in ignore_tokens):
            continue
        if any(token in title.lower() for token in ignore_tokens):
            continue

        events.append(
            Event(
                title=title,
                date="",
                price="",
                url=url,
                source="newsletter_fallback",
            )
        )

    unique = {(e.title, e.url): e for e in events}
    return [asdict(event) for event in unique.values()]
