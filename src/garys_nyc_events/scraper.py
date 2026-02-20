from __future__ import annotations

import re
import time
from dataclasses import asdict
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from .exceptions import ScraperNetworkError
from .http import RequestsHttpClient
from .models import Event
from .protocols import HttpClient


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


class GarysGuideScraper:
    BASE_URL = "https://www.garysguide.com/events"

    def __init__(
        self,
        delay_seconds: float = 1.5,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout_seconds: int = 10,
        http_client: Optional[HttpClient] = None,
    ) -> None:
        self.delay_seconds = delay_seconds
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self._http = http_client or RequestsHttpClient()

    def _headers(self) -> Dict[str, str]:
        return {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    def _fetch_html(self, url: str) -> str:
        time.sleep(self.delay_seconds)
        try:
            response = self._http.get(url, headers=self._headers(), timeout=self.timeout_seconds)
            response.raise_for_status()
            return response.text
        except ScraperNetworkError:
            raise

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

    def _extract_anchor(self, element: Tag) -> Optional[Tuple[str, str]]:
        link = element.find("a", href=True)
        if not link:
            return None

        title = self._clean(link.get_text())
        href = self._clean(link.get("href"))
        if not title or not href:
            return None
        return title, href

    def _extract_date_from_table_row(self, cells: List[Tag]) -> str:
        if not cells:
            return ""
        return self._extract_date(self._clean(cells[0].get_text(" ")))

    def _extract_price_from_table_row(self, cells: List[Tag]) -> str:
        if len(cells) <= 1:
            return ""
        return self._extract_price(self._clean(cells[-1].get_text(" ")))

    def _extract_date_and_price_from_element(self, element: Tag) -> Tuple[str, str]:
        date = ""
        price = ""

        if element.name == "tr":
            cells = element.find_all("td")
            date = self._extract_date_from_table_row(cells)
            price = self._extract_price_from_table_row(cells)

        text_blob = self._clean(element.get_text(" "))
        if not date:
            date = self._extract_date(text_blob)
        if not price:
            price = self._extract_price(text_blob)
        return date, price

    def _extract_event_from_element(self, element: Tag) -> Optional[Event]:
        anchor = self._extract_anchor(element)
        if anchor is None:
            return None

        title, href = anchor
        url = self._normalize_url(href)
        date, price = self._extract_date_and_price_from_element(element)
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

        unique = {}
        for event in events:
            key = (event.title, event.url)
            unique[key] = event

        return [asdict(event) for event in unique.values()]

    def get_events(self) -> List[Dict[str, str]]:
        html = self._fetch_html(self.BASE_URL)
        return self.parse_events(html)


def scrape_default_garys_guide(delay_seconds: float = 1.5) -> List[Dict[str, str]]:
    return GarysGuideScraper(delay_seconds=delay_seconds).get_events()
