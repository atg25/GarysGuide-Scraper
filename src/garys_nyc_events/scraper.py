from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, asdict
from typing import Iterable, List, Dict, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)

EVENT_LINK_FRAGMENT = "/events/"
PRICE_REGEX = re.compile(r"\bFREE\b|\$\s?\d+(?:\.\d{2})?", re.IGNORECASE)
DATE_TOKENS = [
    "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun",
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


@dataclass(frozen=True)
class Event:
    title: str
    date: str
    price: str
    url: str
    source: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


class GarysGuideScraper:
    BASE_URL = "https://www.garysguide.com/events"

    def __init__(
        self,
        delay_seconds: float = 1.5,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout_seconds: int = 10,
    ) -> None:
        self.delay_seconds = delay_seconds
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds

    def _headers(self) -> Dict[str, str]:
        return {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    def _fetch_html(self, url: str) -> str:
        time.sleep(self.delay_seconds)
        response = requests.get(url, headers=self._headers(), timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.text

    def _clean(self, value: Optional[str]) -> str:
        return value.strip() if value else ""

    def _normalize_url(self, href: str) -> str:
        return urljoin(self.BASE_URL, href)

    def _extract_price(self, text: str) -> str:
        normalized = " ".join(text.split())
        if not normalized:
            return ""
        match = PRICE_REGEX.search(normalized)
        if not match:
            return ""
        token = match.group(0)
        return "FREE" if "free" in token.lower() else token.replace(" ", "")

    def _extract_date(self, text: str) -> str:
        normalized = " ".join(text.split())
        if not normalized:
            return ""
        if any(token in normalized for token in DATE_TOKENS):
            return normalized
        return ""

    def _extract_event_from_element(self, element: Tag) -> Optional[Event]:
        link = element.find("a", href=True)
        if not link:
            return None

        title = self._clean(link.get_text())
        url = self._clean(link.get("href"))
        if not title or not url:
            return None

        url = self._normalize_url(url)

        text_blob = self._clean(element.get_text(" "))
        date = ""
        price = ""

        if element.name == "tr":
            cells = element.find_all("td")
            if cells:
                date = self._extract_date(self._clean(cells[0].get_text(" ")))
                if len(cells) > 1:
                    price = self._extract_price(self._clean(cells[-1].get_text(" ")))

        if not date:
            date = self._extract_date(text_blob)
        if not price:
            price = self._extract_price(text_blob)

        return Event(title=title, date=date, price=price, url=url, source="garysguide_web")

    def _candidate_elements(self, soup: BeautifulSoup) -> Iterable[Tag]:
        for link in soup.select("a[href]"):
            href = link.get("href", "")
            if EVENT_LINK_FRAGMENT not in href:
                continue
            container = link.find_parent(["tr", "li", "div", "article"])
            yield container if container else link

    def parse_events(self, html: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        events: List[Event] = []

        for element in self._candidate_elements(soup):
            event = self._extract_event_from_element(element)
            if event:
                events.append(event)

        # Deduplicate by URL and title
        unique = {}
        for event in events:
            key = (event.title, event.url)
            unique[key] = event

        return [event.to_dict() for event in unique.values()]

    def get_events(self) -> List[Dict[str, str]]:
        html = self._fetch_html(self.BASE_URL)
        return self.parse_events(html)

    def get_events_safe(self) -> List[Dict[str, str]]:
        try:
            return self.get_events()
        except requests.RequestException:
            return []


def get_events(delay_seconds: float = 1.5) -> List[Dict[str, str]]:
    return GarysGuideScraper(delay_seconds=delay_seconds).get_events()


def get_events_safe(delay_seconds: float = 1.5) -> List[Dict[str, str]]:
    return GarysGuideScraper(delay_seconds=delay_seconds).get_events_safe()


def filter_events_by_keyword(
    events: List[Dict[str, str]],
    keyword: str,
) -> List[Dict[str, str]]:
    needle = keyword.lower().strip()
    if not needle:
        return events
    return [event for event in events if needle in event.get("title", "").lower()]


def get_events_ai_json(delay_seconds: float = 1.5) -> str:
    events = get_events_safe(delay_seconds=delay_seconds)
    ai_events = filter_events_by_keyword(events, "AI")
    return json.dumps(ai_events, ensure_ascii=False, indent=2)


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
    return [event.to_dict() for event in unique.values()]
