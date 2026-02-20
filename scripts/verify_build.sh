#!/usr/bin/env bash
set -euo pipefail

poetry build

echo "Build artifacts:"
ls -la dist

docker build -t garys-nyc-events:test .

if docker run --rm garys-nyc-events:test which cron >/dev/null 2>&1; then
	echo "FAIL: cron found in image"
	exit 1
fi

echo "OK: no cron binary in image"

set +e
docker run --rm -e DB_PATH=/tmp/garys_events.db garys-nyc-events:test
run_exit=$?
set -e

if [[ "$run_exit" -ne 0 && "$run_exit" -ne 1 ]]; then
	echo "FAIL: one-shot container returned unexpected exit code: $run_exit"
	exit 1
fi

echo "OK: one-shot container exits cleanly (0 or 1)"
