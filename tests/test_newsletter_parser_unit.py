from pathlib import Path

from garys_nyc_events.newsletter_parser import parse_newsletter_html


def test_parse_newsletter_html_extracts_events():
    html = Path("tests/fixtures/sample_newsletter.html").read_text()
    events = parse_newsletter_html(html)

    assert len(events) == 2
    assert events[0]["title"] == "Alpha Event"


def test_parse_newsletter_html_ignores_unsubscribe_links():
    html = "<a href='https://example.com/unsubscribe'>Unsubscribe</a>"
    events = parse_newsletter_html(html)
    assert events == []
