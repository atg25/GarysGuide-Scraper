FROM python:3.12-slim AS build

WORKDIR /app

COPY pyproject.toml README.md LICENSE CHANGELOG.md /app/
COPY src /app/src

RUN pip install --no-cache-dir --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /wheels .


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends sqlite3 cron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=build /wheels /wheels
COPY scripts /app/scripts

RUN pip install --no-cache-dir /wheels/*.whl \
    && rm -rf /wheels \
    && chmod +x /app/scripts/run_once_entrypoint.sh \
                /app/scripts/verify_db.sh \
                /app/scripts/start_cron.sh

ENV SCRAPER_STRATEGY="web" \
    SCRAPER_SEARCH_TERM="" \
    SCRAPER_LIMIT="0" \
    DB_PATH="/data/garys_events.db" \
    RETRY_ATTEMPTS="3" \
    RETRY_BACKOFF_SECONDS="5" \
    API_TOKEN="" \
    GEMINI_API_KEY="" \
    TAGGING_ENABLED="true" \
    CRON_SCHEDULE="0 8 * * *"

VOLUME ["/data"]

CMD ["garys-events-run-once"]
