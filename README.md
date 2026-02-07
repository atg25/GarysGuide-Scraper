# garys_nyc_events

A polite, dependency-light Python library for extracting NYC tech events from GarysGuide.

## Features

- Scrapes the GarysGuide events page
- Polite throttling and a browser-like User-Agent
- Extracts title, date, price (including "FREE"), and URL
- Includes a newsletter HTML fallback parser

## Install

```bash
pip install garys_nyc_events
```

## PyPI + Poetry Setup

```bash
poetry install
```

### Publish to PyPI

```bash
poetry build
poetry publish
```

## Releases (GitHub → PyPI)

This repo includes a GitHub Actions workflow that publishes to PyPI when you push a version tag.

1. Add a GitHub repo secret named `PYPI_API_TOKEN` with your PyPI API token.
2. Ensure `tool.poetry.version` in `pyproject.toml` is set.
3. Create and push a matching tag:

```bash
git tag v0.1.1
git push origin v0.1.1
```

The workflow verifies the tag matches `v{version}`, runs tests, builds, checks the dist, then publishes.

### Publish to TestPyPI

```bash
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry publish -r testpypi
```

### Configure PyPI Token (Recommended)

```bash
poetry config pypi-token.pypi YOUR_TOKEN
```

## Usage

```python
from garys_nyc_events import (
	GarysGuideScraper,
	get_events,
	get_events_ai_json,
	get_events_safe,
	parse_newsletter_html,
)

# Live scrape (polite delay included)
events = get_events()

# Safe mode: returns [] instead of raising on network errors
events = get_events_safe()

# JSON output of AI-related events (filtered by title)
ai_events_json = get_events_ai_json()
print(ai_events_json)

# Parse raw HTML from a newsletter export
raw_html = "<html>...your email html...</html>"
newsletter_events = parse_newsletter_html(raw_html)

# Class-based usage (custom delay)
scraper = GarysGuideScraper(delay_seconds=2.0)
events = scraper.get_events()
```

## How the Scraper Works

- Selects anchors where href contains `/events/`
- Walks up to the nearest `tr`, `li`, `div`, or `article` to capture context
- If the container is a table row, it uses the first cell for date and the last cell for price
- Extracts prices using `$` amounts or `FREE`
- Normalizes relative URLs to full URLs

## Notes

- The public API returns a list of dictionaries with keys: `title`, `date`, `price`, `url`, `source`.
- The scraper is polite by default; adjust `delay_seconds` if needed.
- Live E2E test is disabled by default. Run with `RUN_E2E=1` to enable.

## Development

```bash
poetry install
poetry run pytest
```

### Verify Build Artifacts

```bash
./scripts/verify_build.sh
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT
