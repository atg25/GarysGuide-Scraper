#!/usr/bin/env bash
set -euo pipefail

DB_PATH="${1:-${DB_PATH:-/data/garys_events.db}}"

if [[ ! -f "${DB_PATH}" ]]; then
  echo "Database file not found: ${DB_PATH}"
  exit 1
fi

echo "== verify_schema.sql =="
sqlite3 "${DB_PATH}" < scripts/sql/verify_schema.sql

echo "== verify_latest_runs.sql =="
sqlite3 "${DB_PATH}" < scripts/sql/verify_latest_runs.sql

echo "== verify_snapshot_counts.sql =="
sqlite3 "${DB_PATH}" < scripts/sql/verify_snapshot_counts.sql
