from importlib.metadata import PackageNotFoundError, version

from .filters import filter_events_by_keyword
from .formatters import get_events_ai_json
from .models import Event
from .newsletter_parser import parse_newsletter_html
from .protocols import EventScraper, EventStore, HttpClient, HttpResponse
from .scraper import GarysGuideScraper, scrape_default_garys_guide

try:
    __version__ = version("garys_nyc_events")
except PackageNotFoundError:  # pragma: no cover - local editable usage
    __version__ = "0.0.0"

__all__ = [
    "Event",
    "GarysGuideScraper",
    "EventScraper",
    "EventStore",
    "HttpClient",
    "HttpResponse",
    "filter_events_by_keyword",
    "scrape_default_garys_guide",
    "get_events_ai_json",
    "parse_newsletter_html",
    "__version__",
]
