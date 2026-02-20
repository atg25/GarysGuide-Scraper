from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from garys_nyc_events.exceptions import ScraperNetworkError, ScraperTimeoutError
from garys_nyc_events.scraper import GarysGuideScraper
from tests.http_doubles import FailingHttpClient, StubHttpClient, StubHttpResponse


def _first_tag(html: str):
    return BeautifulSoup(html, "html.parser").find()


def test_parse_events_extracts_basic_fields():
    html = Path("tests/fixtures/sample_events_page.html").read_text()
    scraper = GarysGuideScraper(delay_seconds=0)

    events = scraper.parse_events(html)

    assert len(events) == 2
    titles = {event["title"] for event in events}
    urls = {event["url"] for event in events}
    prices = {event["price"] for event in events}
    dates = {event["date"] for event in events}

    assert "NYC Tech Meetup" in titles
    assert any(url.startswith("https://www.garysguide.com/") and url.endswith("/123") for url in urls)
    assert "FREE" in prices
    assert "$10" in prices
    assert any("Thu Feb 06" in date for date in dates)


def test_parse_events_handles_empty_html():
    scraper = GarysGuideScraper(delay_seconds=0)
    events = scraper.parse_events("<html></html>")
    assert events == []


def test_extract_anchor_returns_none_when_no_link():
    scraper = GarysGuideScraper(delay_seconds=0)
    element = _first_tag("<div>No link</div>")
    assert element is not None
    assert scraper._extract_anchor(element) is None


def test_extract_anchor_returns_none_when_title_empty():
    scraper = GarysGuideScraper(delay_seconds=0)
    element = _first_tag("<div><a href='/events/x'> </a></div>")
    assert element is not None
    assert scraper._extract_anchor(element) is None


def test_extract_anchor_returns_title_and_href():
    scraper = GarysGuideScraper(delay_seconds=0)
    element = _first_tag("<div><a href='/events/x'>Title</a></div>")
    assert element is not None
    assert scraper._extract_anchor(element) == ("Title", "/events/x")


def test_extract_date_from_table_row_first_cell():
    scraper = GarysGuideScraper(delay_seconds=0)
    row = _first_tag("<tr><td>Mon Jan 6</td><td>Event</td></tr>")
    assert row is not None
    cells = row.find_all("td")
    assert scraper._extract_date_from_table_row(cells) == "Mon Jan 6"


def test_extract_price_from_table_row_last_cell():
    scraper = GarysGuideScraper(delay_seconds=0)
    row = _first_tag("<tr><td>Mon Jan 6</td><td>Event</td><td>$25</td></tr>")
    assert row is not None
    cells = row.find_all("td")
    assert scraper._extract_price_from_table_row(cells) == "$25"


def test_extract_date_and_price_prefers_table_row():
    scraper = GarysGuideScraper(delay_seconds=0)
    row = _first_tag("<tr><td>Thu Feb 06</td><td><a href='/events/1'>AI Event</a></td><td>FREE</td></tr>")
    assert row is not None
    date, price = scraper._extract_date_and_price_from_element(row)
    assert date == "Thu Feb 06"
    assert price == "FREE"


def test_extract_date_and_price_falls_back_to_blob():
    scraper = GarysGuideScraper(delay_seconds=0)
    element = _first_tag("<div><a href='/events/1'>AI Event</a> Thu Feb 06 FREE</div>")
    assert element is not None
    date, price = scraper._extract_date_and_price_from_element(element)
    assert "Thu Feb 06" in date
    assert price == "FREE"


def test_scraper_uses_injected_http_client():
    html = Path("tests/fixtures/sample_events_page.html").read_text()
    client = StubHttpClient([StubHttpResponse(text=html)])
    scraper = GarysGuideScraper(delay_seconds=0, http_client=client)
    events = scraper.get_events()
    assert client.calls == 1
    assert len(events) == 2


def test_fetch_html_raises_scraper_network_error_on_connection_error():
    scraper = GarysGuideScraper(delay_seconds=0, http_client=FailingHttpClient())
    with pytest.raises(ScraperNetworkError):
        scraper.get_events()


def test_fetch_html_raises_scraper_timeout_error_on_timeout():
    scraper = GarysGuideScraper(
        delay_seconds=0,
        http_client=FailingHttpClient(exc=ScraperTimeoutError("timeout")),
    )
    with pytest.raises(ScraperTimeoutError):
        scraper.get_events()


def test_fetch_html_raises_scraper_network_error_on_http_error():
    client = StubHttpClient([StubHttpResponse(text="bad", status_code=500)])
    scraper = GarysGuideScraper(delay_seconds=0, http_client=client)
    with pytest.raises(ScraperNetworkError):
        scraper.get_events()
