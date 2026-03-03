from pathlib import Path

import pytest
import requests
from bs4 import BeautifulSoup

from garys_nyc_events.exceptions import ScraperNetworkError, ScraperTimeoutError
from garys_nyc_events.http import RequestsHttpClient
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
    assert all("time" in event for event in events)
    assert all("location" in event for event in events)
    assert all("description" in event for event in events)


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


def test_extract_time_finds_seven_pm():
    scraper = GarysGuideScraper(delay_seconds=0)
    assert scraper._extract_time("Join us Thu Jan 23 at 7:00 PM NYC") == "7:00 PM"


def test_extract_time_returns_empty_for_no_time():
    scraper = GarysGuideScraper(delay_seconds=0)
    assert scraper._extract_time("No time here") == ""


def test_extract_date_does_not_false_match_month_substring_inside_word():
    scraper = GarysGuideScraper(delay_seconds=0)
    assert scraper._extract_date("Marketing Mixer Cloud One Lounge") == ""


def test_extract_location_returns_venue_text():
    scraper = GarysGuideScraper(delay_seconds=0)
    element = _first_tag("<div><span class='venue'>Midtown NYC</span></div>")
    assert element is not None
    assert scraper._extract_location(element) == "Midtown NYC"


def test_extract_location_returns_empty_when_absent():
    scraper = GarysGuideScraper(delay_seconds=0)
    element = _first_tag("<div><span>no venue marker</span></div>")
    assert element is not None
    assert scraper._extract_location(element) == ""


def test_extract_location_from_text_fallback():
    scraper = GarysGuideScraper(delay_seconds=0)
    text = "AI Demo Series Thu Feb 27 7:00 PM Cloud One Lounge, 133 Greenwich St With Biddable Media"
    location = scraper._extract_location_from_text(
        text,
        title="AI Demo Series",
        date="Thu Feb 27",
        time_value="7:00 PM",
        price="",
    )
    assert "Cloud One Lounge" in location


def test_extract_description_from_fgray():
    scraper = GarysGuideScraper(delay_seconds=0)
    element = _first_tag(
        "<td><font class='fgray'>With Jane Doe (CEO, Acme) , John Smith (CTO, Startup) .</font></td>"
    )
    assert element is not None
    description = scraper._extract_description(element)
    assert "Jane Doe" in description
    assert "John Smith" in description


def test_extract_description_truncates_at_500():
    scraper = GarysGuideScraper(delay_seconds=0)
    long_text = "w" * 600
    element = _first_tag(f"<div><font class='fgray'>{long_text}</font></div>")
    assert element is not None
    description = scraper._extract_description(element)
    assert len(description) == 500


def test_extract_description_empty_without_fgray():
    scraper = GarysGuideScraper(delay_seconds=0)
    element = _first_tag("<div>Some text but no fgray element</div>")
    assert element is not None
    description = scraper._extract_description(element)
    assert description == ""


def test_extract_event_from_element_is_pure_delegation():
    scraper = GarysGuideScraper(delay_seconds=0)
    element = _first_tag("<div><a href='/events/1'>AI Event</a></div>")
    assert element is not None

    calls = {
        "anchor": 0,
        "build": 0,
    }

    def fake_extract_anchor(tag):
        calls["anchor"] += 1
        assert tag is element
        return ("AI Event", "/events/1")

    def fake_build_event(tag, anchor):
        calls["build"] += 1
        assert tag is element
        assert anchor == ("AI Event", "/events/1")
        return None

    scraper._extract_anchor = fake_extract_anchor  # type: ignore[method-assign]
    scraper._build_event_from_anchor = fake_build_event  # type: ignore[method-assign]

    result = scraper._extract_event_from_element(element)

    assert result is None
    assert calls["anchor"] == 1
    assert calls["build"] == 1


def test_parse_events_extracts_date_and_time_from_outer_table_row_structure():
        html = """
        <table>
            <tr>
                <td align='center' valign='top' width='48'><b>Feb 25</b><br/>7:00pm</td>
                <td>&nbsp;</td>
                <td align='center' width='37' valign='top'>$20</td>
                <td>&nbsp;</td>
                <td align='left' valign='top'>
                    <table width='100%'><tr><td align='left'>
                        <font class='ftitle'><a href='https://www.garysguide.com/events/x/Marketing-Mixer'><b>Marketing Mixer</b></a></font>
                        <font class='fdescription'><br/><b>Cloud One Lounge</b>, 133 Greenwich St</font>
                    </td></tr></table>
                </td>
            </tr>
        </table>
        """
        scraper = GarysGuideScraper(delay_seconds=0)
        events = scraper.parse_events(html)
        assert len(events) == 1
        assert events[0]["date"] == "Feb 25"
        assert events[0]["time"] == "7:00PM"
        assert "Cloud One Lounge" in events[0]["location"]


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


def test_scraper_network_error_chains_original_cause(monkeypatch):
    def fake_get(*_args, **_kwargs):
        raise requests.ConnectionError("connection failed")

    monkeypatch.setattr(requests, "get", fake_get)
    scraper = GarysGuideScraper(delay_seconds=0, http_client=RequestsHttpClient())

    with pytest.raises(ScraperNetworkError) as exc_info:
        scraper.get_events()

    assert isinstance(exc_info.value.__cause__, requests.RequestException)
    assert isinstance(exc_info.value.cause, requests.RequestException)


def test_scraper_has_no_get_events_safe_method():
    scraper = GarysGuideScraper(delay_seconds=0)
    assert hasattr(scraper, "get_events_safe") is False
