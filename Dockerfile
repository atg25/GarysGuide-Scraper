FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md LICENSE CHANGELOG.md /app/
COPY src /app/src
COPY scripts /app/scripts

RUN pip install --no-cache-dir . \
    && chmod +x /app/scripts/run_once_entrypoint.sh /app/scripts/verify_db.sh

ENV SCRAPER_STRATEGY="web" \
    SCRAPER_SEARCH_TERM="" \
    SCRAPER_LIMIT="0" \
    DB_PATH="/data/garys_events.db" \
    RETRY_ATTEMPTS="3" \
    RETRY_BACKOFF_SECONDS="5" \
    API_TOKEN=""

VOLUME ["/data"]

CMD ["/app/scripts/run_once_entrypoint.sh"]
