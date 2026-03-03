#!/usr/bin/env bash
set -euo pipefail

docker build -t garys-nyc-events:test .

if docker run --rm garys-nyc-events:test which cron >/dev/null 2>&1; then
	echo "FAIL: cron found in image"
	exit 1
fi

echo "OK: no cron binary in image"

set +e
run_output="$(docker run --rm -e DB_PATH=/tmp/garys_events.db garys-nyc-events:test 2>&1)"
run_exit=$?
set -e

if [[ "$run_exit" -ne 0 && "$run_exit" -ne 1 ]]; then
	echo "FAIL: one-shot container returned unexpected exit code: $run_exit"
	exit 1
fi

echo "OK: one-shot container exits cleanly (0 or 1)"

if ! grep -q "run_id=" <<<"$run_output"; then
	echo "FAIL: expected run log output containing run_id"
	echo "$run_output"
	exit 1
fi

echo "OK: run logs emitted to stdout"

tmp_data_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_data_dir"' EXIT

set +e
docker run --rm -e DB_PATH=/data/garys_events.db -v "$tmp_data_dir:/data" garys-nyc-events:test >/dev/null 2>&1
mounted_exit=$?
set -e

if [[ "$mounted_exit" -ne 0 && "$mounted_exit" -ne 1 ]]; then
	echo "FAIL: mounted one-shot container returned unexpected exit code: $mounted_exit"
	exit 1
fi

if [[ ! -f "$tmp_data_dir/garys_events.db" ]]; then
	echo "FAIL: expected DB file at mounted path"
	exit 1
fi

echo "OK: DB file created at mounted path"
