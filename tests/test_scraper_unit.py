from pathlib import Path

from garys_nyc_events.scraper import GarysGuideScraper


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
