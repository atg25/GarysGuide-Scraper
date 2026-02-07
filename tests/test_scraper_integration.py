import pytest
import requests
import requests_mock

from garys_nyc_events.scraper import GarysGuideScraper


def test_fetch_html_handles_http_errors():
    scraper = GarysGuideScraper(delay_seconds=0)
    with requests_mock.Mocker() as m:
        m.get(scraper.BASE_URL, status_code=500)
        with pytest.raises(requests.HTTPError):
            scraper.get_events()
