#!/usr/bin/env bash
set -euo pipefail

export SCRAPER_STRATEGY="${SCRAPER_STRATEGY:-web}"
export SCRAPER_SEARCH_TERM="${SCRAPER_SEARCH_TERM:-}"
export SCRAPER_LIMIT="${SCRAPER_LIMIT:-0}"
export DB_PATH="${DB_PATH:-/data/garys_events.db}"
export RETRY_ATTEMPTS="${RETRY_ATTEMPTS:-3}"
export RETRY_BACKOFF_SECONDS="${RETRY_BACKOFF_SECONDS:-5}"
export API_TOKEN="${API_TOKEN:-}"

mkdir -p "$(dirname "${DB_PATH}")"

exec python -m garys_nyc_events.runner_once
