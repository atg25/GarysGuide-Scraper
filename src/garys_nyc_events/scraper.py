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
TIME_REGEX = re.compile(r"\b\d{1,2}:\d{2}\s?(?:AM|PM)\b", re.IGNORECASE)
DATE_REGEXES = [
    re.compile(
        r"\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b\s*"
        r"(?:,\s*)?"
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b\s+\d{1,2}"
        r"(?:,\s*\d{4})?",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b\s+\d{1,2}"
        r"(?:,\s*\d{4})?",
        re.IGNORECASE,
    ),
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
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;"
                "q=0.9,*/*;q=0.8"
            ),
        }

    def _fetch_html(self, url: str) -> str:
        time.sleep(self.delay_seconds)
        try:
            response = self._http.get(
                url,
                headers=self._headers(),
                timeout=self.timeout_seconds,
            )
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
        for pattern in DATE_REGEXES:
            match = pattern.search(normalized)
            if match:
                return match.group(0)
        return ""

    def _extract_time(self, text: str) -> str:
        normalized = " ".join(text.split())
        if not normalized:
            return ""
        match = TIME_REGEX.search(normalized)
        return match.group(0).upper() if match else ""

    def _extract_location(self, element: Tag) -> str:
        # GarysGuide uses font.fdescription for venue + address
        tag = element.select_one("font.fdescription")
        if tag:
            value = " ".join(tag.get_text(" ", strip=True).split())
            if value:
                return value
        # Generic fallback selectors
        for selector in [".venue", ".location", "[class*=venue]", "[class*=location]", "[class*=address]"]:
            tag = element.select_one(selector)
            if tag is None:
                continue
            value = self._clean(tag.get_text(" "))
            if value:
                return value
        return ""

    def _extract_location_from_text(
        self,
        text: str,
        *,
        title: str,
        date: str,
        time_value: str,
        price: str,
    ) -> str:
        working = self._clean(text)
        if not working:
            return ""

        for token in [title, date, time_value, price]:
            cleaned = self._clean(token)
            if cleaned:
                working = working.replace(cleaned, " ")

        lowered = working.lower()
        split_markers = [" with ", " w/ "]
        for marker in split_markers:
            idx = lowered.find(marker)
            if idx != -1:
                working = working[:idx]
                break

        location = self._clean(working).strip("-,:; ")
        return location[:180]

    def _extract_description(self, element: Tag) -> str:
        # GarysGuide stores event details (speakers, notes) in font.fgray
        tag = element.select_one("font.fgray")
        if tag:
            value = " ".join(tag.get_text(" ", strip=True).split())
            if value:
                return value[:500]
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

    def _extract_date_and_price_from_element(
        self,
        element: Tag,
    ) -> Tuple[str, str]:
        if element.name == "tr":
            table_date, table_price = self._extract_date_and_price_from_table(
                element
            )
            if table_date and table_price:
                return table_date, table_price
        return self._extract_date_and_price_from_text_blob(element)

    def _extract_date_and_price_from_table(
        self,
        element: Tag,
    ) -> Tuple[str, str]:
        date = ""
        price = ""

        cells = element.find_all("td")
        date = self._extract_date_from_table_row(cells)
        price = self._extract_price_from_table_row(cells)
        return date, price

    def _extract_date_and_price_from_text_blob(
        self,
        element: Tag,
    ) -> Tuple[str, str]:
        date = ""
        price = ""

        text_blob = self._clean(element.get_text(" "))
        if not date:
            date = self._extract_date(text_blob)
        if not price:
            price = self._extract_price(text_blob)
        return date, price

    def _build_event_from_anchor(
        self,
        element: Tag,
        anchor: Optional[Tuple[str, str]],
    ) -> Optional[Event]:
        if anchor is None:
            return None

        title, href = anchor
        url = self._normalize_url(href)
        text_blob = self._clean(element.get_text(" "))
        date, price = self._extract_date_and_price_from_element(element)
        time_value = self._extract_time(text_blob)
        location = self._extract_location(element)
        if not location:
            location = self._extract_location_from_text(
                text_blob,
                title=title,
                date=date,
                time_value=time_value,
                price=price,
            )
        description = self._extract_description(element)
        return Event(
            title=title,
            date=date,
            price=price,
            url=url,
            source="garysguide_web",
            time=time_value,
            location=location,
            description=description,
        )

    def _events_from_candidates(self, soup: BeautifulSoup) -> List[Event]:
        events: List[Event] = []
        for element in self._candidate_elements(soup):
            event = self._extract_event_from_element(element)
            if event is not None:
                events.append(event)
        return events

    def _deduplicate_events(self, events: List[Event]) -> List[Event]:
        unique = {}
        for event in events:
            key = (event.title, event.url)
            unique[key] = event
        return list(unique.values())

    def _extract_event_from_element(self, element: Tag) -> Optional[Event]:
        anchor = self._extract_anchor(element)
        return self._build_event_from_anchor(element, anchor)

    def _is_outer_event_row(self, row: Tag) -> bool:
        cells = row.find_all("td", recursive=False)
        if len(cells) < 3:
            return False
        date_text = self._clean(cells[0].get_text(" "))
        price_text = self._clean(cells[2].get_text(" ")) if len(cells) > 2 else ""
        has_date = bool(self._extract_date(date_text))
        has_price = bool(self._extract_price(price_text)) or "$" in price_text
        return has_date or has_price

    def _preferred_container(self, link: Tag) -> Tag:
        for row in link.find_parents("tr"):
            if self._is_outer_event_row(row):
                return row
        container = link.find_parent(["tr", "li", "div", "article"])
        return container if container else link

    def _candidate_elements(self, soup: BeautifulSoup) -> Iterable[Tag]:
        for link in soup.select("a[href]"):
            href = link.get("href", "")
            if EVENT_LINK_FRAGMENT not in href:
                continue
            yield self._preferred_container(link)

    def parse_events(self, html: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        events = self._events_from_candidates(soup)
        unique_events = self._deduplicate_events(events)
        return [asdict(event) for event in unique_events]

    def get_events(self) -> List[Dict[str, str]]:
        html = self._fetch_html(self.BASE_URL)
        return self.parse_events(html)


def scrape_default_garys_guide(
    delay_seconds: float = 1.5,
) -> List[Dict[str, str]]:
    return GarysGuideScraper(delay_seconds=delay_seconds).get_events()
