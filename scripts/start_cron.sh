#!/usr/bin/env bash
# Starts the in-container cron daemon that runs the scraper on schedule.
# Debian's cron reads /etc/environment for environment variables, so we dump
# the current Docker env there first so the job inherits GEMINI_API_KEY etc.
set -euo pipefail

# Make the data directory available to the scraper job
mkdir -p "$(dirname "${DB_PATH:-/data/garys_events.db}")"

# Write docker env vars into /etc/environment so crond inherits them
printenv | grep -v '^_' > /etc/environment

# Allow overriding the schedule via CRON_SCHEDULE env var; default is 8am daily
SCHEDULE="${CRON_SCHEDULE:-0 8 * * *}"

echo "${SCHEDULE} /app/scripts/run_once_entrypoint.sh >> /var/log/garys_cron.log 2>&1" | crontab -

echo "Cron scheduler started — job will run on schedule: ${SCHEDULE}"
echo "Logs will be written to /var/log/garys_cron.log"

exec cron -f
