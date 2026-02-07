import os
import pytest

from garys_nyc_events.scraper import get_events


@pytest.mark.e2e
@pytest.mark.skipif(os.getenv("RUN_E2E") != "1", reason="Set RUN_E2E=1 to enable live test")
def test_live_site_scrape():
    events = get_events(delay_seconds=2.0)
    assert isinstance(events, list)
