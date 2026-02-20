import os
import pytest

from garys_nyc_events.scraper import scrape_default_garys_guide


@pytest.mark.e2e
@pytest.mark.skipif(os.getenv("RUN_E2E") != "1", reason="Set RUN_E2E=1 to enable live test")
def test_live_site_scrape():
    events = scrape_default_garys_guide(delay_seconds=2.0)
    assert isinstance(events, list)
