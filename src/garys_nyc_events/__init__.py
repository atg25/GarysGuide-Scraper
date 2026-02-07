from importlib.metadata import PackageNotFoundError, version

from .scraper import (
	Event,
	GarysGuideScraper,
	filter_events_by_keyword,
	get_events,
	get_events_ai_json,
	get_events_safe,
	parse_newsletter_html,
)

try:
	__version__ = version("garys_nyc_events")
except PackageNotFoundError:  # pragma: no cover - local editable usage
	__version__ = "0.0.0"

__all__ = [
	"Event",
	"GarysGuideScraper",
	"filter_events_by_keyword",
	"get_events",
	"get_events_ai_json",
	"get_events_safe",
	"parse_newsletter_html",
	"__version__",
]
