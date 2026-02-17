#!/usr/bin/env bash
set -euo pipefail

export TZ="${TZ:-UTC}"
export CRON_SCHEDULE="${CRON_SCHEDULE:-0 */6 * * *}"
export SCRAPER_STRATEGY="${SCRAPER_STRATEGY:-web}"
export SCRAPER_SEARCH_TERM="${SCRAPER_SEARCH_TERM:-}"
export SCRAPER_LIMIT="${SCRAPER_LIMIT:-0}"
export DB_PATH="${DB_PATH:-/data/garys_events.db}"
export RETRY_ATTEMPTS="${RETRY_ATTEMPTS:-3}"
export RETRY_BACKOFF_SECONDS="${RETRY_BACKOFF_SECONDS:-5}"
export API_TOKEN="${API_TOKEN:-}"

python -m garys_nyc_events.scheduler --schedule "${CRON_SCHEDULE}"

mkdir -p "$(dirname "${DB_PATH}")"

cat >/etc/cron.d/garys-events <<EOF
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
TZ=${TZ}
CRON_SCHEDULE=${CRON_SCHEDULE}
SCRAPER_STRATEGY=${SCRAPER_STRATEGY}
SCRAPER_SEARCH_TERM=${SCRAPER_SEARCH_TERM}
SCRAPER_LIMIT=${SCRAPER_LIMIT}
DB_PATH=${DB_PATH}
RETRY_ATTEMPTS=${RETRY_ATTEMPTS}
RETRY_BACKOFF_SECONDS=${RETRY_BACKOFF_SECONDS}
API_TOKEN=${API_TOKEN}
${CRON_SCHEDULE} root cd /app && /usr/local/bin/python -m garys_nyc_events.runner_once >> /proc/1/fd/1 2>> /proc/1/fd/2
EOF

chmod 0644 /etc/cron.d/garys-events
crontab /etc/cron.d/garys-events

echo "Running initial one-shot scrape before cron loop"
python -m garys_nyc_events.runner_once

echo "Starting cron in foreground"
exec cron -f
