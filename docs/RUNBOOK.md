# Runbook

## Local One-Shot Pipeline Run

1. Install dependencies:

```bash
poetry install
```

1. Execute one run and persist to SQLite:

```bash
DB_PATH=./garys_events.db poetry run garys-events-run-once
```

1. Verify DB contents:

```bash
DB_PATH=./garys_events.db ./scripts/verify_db.sh
```

## Docker One-Shot Run

1. Build image:

```bash
docker compose build scraper
```

1. Run a single scrape and exit:

```bash
docker compose run --rm scraper
```

1. Verify persistent SQLite state:

```bash
docker compose run --rm scraper /app/scripts/verify_db.sh /data/garys_events.db
```

## Scheduling with Host Cron

Containers are intentionally one-shot. Schedule them externally on the host:

```bash
*/30 * * * * cd /path/to/PyPack_GarysGuide && docker compose run --rm scraper
```

This keeps the container single-process and lets cron remain the scheduler.

## Scheduling with Kubernetes CronJob

Use [deploy/k8s-cronjob.yaml](../deploy/k8s-cronjob.yaml) as the reference job definition.

Apply:

```bash
kubectl apply -f deploy/k8s-cronjob.yaml
```

## DB Verification Commands

```bash
sqlite3 ./garys_events.db < scripts/sql/verify_schema.sql
sqlite3 ./garys_events.db < scripts/sql/verify_latest_runs.sql
sqlite3 ./garys_events.db < scripts/sql/verify_snapshot_counts.sql
```

## Cron in Container

- The `scheduler` service runs cron in the container and triggers `/app/scripts/run_once_entrypoint.sh` on `CRON_SCHEDULE`.
- Scheduler logs are written to `/var/log/garys_cron.log`; scrape logs continue to emit run summaries for visibility.
- For external orchestrators, keep using `scraper` as one-shot and schedule that service outside Docker.
