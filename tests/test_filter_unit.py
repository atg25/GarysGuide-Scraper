from garys_nyc_events.filters import filter_events_by_keyword


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
