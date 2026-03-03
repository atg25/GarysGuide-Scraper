from datetime import date

from garys_nyc_events.filters import filter_events_by_keyword
from garys_nyc_events.filters import filter_ai_events, filter_events_upcoming_week


def test_filter_events_by_keyword_matches_title():
    events = [
        {"title": "AI Founders Night"},
        {"title": "Product Meetup"},
    ]

    filtered = filter_events_by_keyword(events, "ai")
    assert len(filtered) == 1
    assert filtered[0]["title"] == "AI Founders Night"


def test_filter_events_by_keyword_empty_returns_all():
    events = [{"title": "AI Summit"}]
    assert filter_events_by_keyword(events, "") == events


def test_filter_upcoming_week_excludes_yesterday():
    events = [{"title": "AI", "date": "2026-02-25"}]
    filtered = filter_events_upcoming_week(events, today=date(2026, 2, 26))
    assert filtered == []


def test_filter_upcoming_week_includes_tomorrow():
    events = [{"title": "AI", "date": "2026-02-27"}]
    filtered = filter_events_upcoming_week(events, today=date(2026, 2, 26))
    assert len(filtered) == 1


def test_filter_upcoming_week_excludes_eight_days_out():
    events = [{"title": "AI", "date": "2026-03-06"}]
    filtered = filter_events_upcoming_week(events, today=date(2026, 2, 26))
    assert filtered == []


def test_filter_upcoming_week_excludes_empty_date():
    events = [{"title": "AI", "date": ""}]
    filtered = filter_events_upcoming_week(events, today=date(2026, 2, 26))
    assert filtered == []


def test_filter_ai_events_keeps_ai_title():
    events = [{"title": "NYC AI Summit", "description": ""}]
    filtered = filter_ai_events(events)
    assert len(filtered) == 1


def test_filter_ai_events_drops_non_ai():
    events = [{"title": "Wine & Cheese", "description": ""}]
    filtered = filter_ai_events(events)
    assert filtered == []


def test_filter_ai_events_matches_description_keyword():
    events = [{"title": "Founder Meetup", "description": "machine learning demos"}]
    filtered = filter_ai_events(events)
    assert len(filtered) == 1
