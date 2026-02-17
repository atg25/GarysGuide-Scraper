# Requirements Traceability

| Requirement | Implementation Artifact | Verification Step |
|---|---|---|
| Persist scraper output to SQLite | `src/garys_nyc_events/storage.py` (`runs`, `products`, `product_snapshots`) | `pytest tests/test_storage_unit.py` |
| One-shot runner command | `src/garys_nyc_events/runner_once.py`, script `garys-events-run-once` | `DB_PATH=./local_events.db poetry run garys-events-run-once` |
| Cron schedule parsing | `src/garys_nyc_events/scheduler.py` | `pytest tests/test_scheduler_unit.py::test_validate_cron_schedule_positive` |
| Retry/backoff transient failures | `run_once()` + `is_transient_error()` | `pytest tests/test_scheduler_unit.py::test_retry_on_transient_error` |
| No retry on non-transient errors | `run_once()` retry guard | `pytest tests/test_scheduler_unit.py::test_no_retry_on_non_transient_error` |
| Run status classification (`success/partial/failure`) | `run_once()` status logic + `runs.status` | `pytest tests/test_storage_unit.py tests/test_scheduler_unit.py` |
| Cron runtime in container | `scripts/start-cron.sh`, `Dockerfile` | `docker compose logs -f scheduler` |
| SQLite persistence volume | `docker-compose.yml` named volume `garys_events_data` | `docker compose down && docker compose up -d` then verify rows still exist |
| Config contract via env vars | `src/garys_nyc_events/config.py`, `docker-compose.yml`, `scripts/start-cron.sh` | `env` overrides + one-shot run |
| SQL verification scripts | `scripts/sql/*.sql`, `scripts/verify_db.sh` | `./scripts/verify_db.sh <db_path>` |
| Tests remain green | existing and new tests under `tests/` | `poetry run pytest` |
