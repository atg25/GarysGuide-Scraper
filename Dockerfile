FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends cron sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md LICENSE CHANGELOG.md /app/
COPY src /app/src
COPY scripts /app/scripts

RUN pip install --no-cache-dir . \
    && chmod +x /app/scripts/start-cron.sh /app/scripts/verify_db.sh

ENV CRON_SCHEDULE="0 */6 * * *" \
    TZ="UTC" \
    SCRAPER_STRATEGY="web" \
    SCRAPER_SEARCH_TERM="" \
    SCRAPER_LIMIT="0" \
    DB_PATH="/data/garys_events.db" \
    RETRY_ATTEMPTS="3" \
    RETRY_BACKOFF_SECONDS="5" \
    API_TOKEN=""

VOLUME ["/data"]

CMD ["/app/scripts/start-cron.sh"]
