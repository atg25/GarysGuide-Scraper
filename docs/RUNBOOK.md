# Runbook

## Local One-Shot Pipeline Run

1. Install dependencies:

```bash
poetry install
```

2. Execute one run and persist to SQLite:

```bash
DB_PATH=./local_events.db poetry run garys-events-run-once
```

3. Verify DB contents:

```bash
DB_PATH=./local_events.db ./scripts/verify_db.sh
```

## Docker Scheduled Pipeline Run

1. Build and start scheduler container:

```bash
docker compose up --build -d
```

2. Follow logs (run summaries every execution):

```bash
docker compose logs -f scheduler
```

3. Verify persistent SQLite state inside container:

```bash
docker compose exec scheduler /app/scripts/verify_db.sh /data/garys_events.db
```

4. Stop stack (volume retained):

```bash
docker compose down
```

5. Remove stack + data volume explicitly:

```bash
docker compose down -v
```

## DB Verification Commands

```bash
sqlite3 ./local_events.db < scripts/sql/verify_schema.sql
sqlite3 ./local_events.db < scripts/sql/verify_latest_runs.sql
sqlite3 ./local_events.db < scripts/sql/verify_snapshot_counts.sql
```

## Troubleshooting

- If cron fails to start, validate schedule manually:

```bash
poetry run garys-events-validate-cron --schedule "0 */6 * * *"
```

- If no rows are written, inspect run logs for `status=failure` and error details.
- Ensure `DB_PATH` points to a writable file path.
