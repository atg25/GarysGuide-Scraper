from dataclasses import asdict

from garys_nyc_events.filters import filter_events_by_keyword
from garys_nyc_events.formatters import get_events_ai_json
from garys_nyc_events.models import Event
from garys_nyc_events.newsletter_parser import parse_newsletter_html
import garys_nyc_events.scraper as scraper_module


def test_event_has_no_to_dict_method():
    event = Event(
        title="AI Meetup",
        date="Thu Feb 06",
        price="FREE",
        url="https://www.garysguide.com/events/1",
        source="garysguide_web",
    )
    assert hasattr(event, "to_dict") is False


def test_asdict_produces_expected_keys():
    event = Event(
        title="AI Meetup",
        date="Thu Feb 06",
        price="FREE",
        url="https://www.garysguide.com/events/1",
        source="garysguide_web",
    )
    payload = asdict(event)
    assert set(payload.keys()) == {
        "title",
        "date",
        "price",
        "url",
        "source",
        "time",
        "location",
        "description",
        "tags",
    }


def test_filter_events_by_keyword_is_importable_from_filters():
    assert callable(filter_events_by_keyword)


def test_parse_newsletter_html_importable_from_newsletter_parser():
    assert callable(parse_newsletter_html)


def test_scraper_module_does_not_define_filter_function():
    assert hasattr(scraper_module, "filter_events_by_keyword") is False


def test_get_events_ai_json_importable_from_formatters():
    assert callable(get_events_ai_json)
