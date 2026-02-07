import requests_mock

from garys_nyc_events import get_events_safe


def test_get_events_safe_returns_empty_list_on_errors():
    with requests_mock.Mocker() as m:
        m.get("https://www.garysguide.com/events", status_code=500)
        assert get_events_safe(delay_seconds=0) == []
