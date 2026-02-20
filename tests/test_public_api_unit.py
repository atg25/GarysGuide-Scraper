import garys_nyc_events
from garys_nyc_events import Event, EventScraper, EventStore, GarysGuideScraper, scrape_default_garys_guide


def test_public_api_exports():
    assert Event
    assert GarysGuideScraper
    assert EventScraper
    assert EventStore
    assert scrape_default_garys_guide
    assert not hasattr(garys_nyc_events, "get_events_safe")
