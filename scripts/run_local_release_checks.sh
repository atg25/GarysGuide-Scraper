#!/usr/bin/env bash
set -euo pipefail

# One-command local quality gate wrapper for PyPack.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -x ".test-venv/bin/python" ]]; then
  PYTHON_BIN=".test-venv/bin/python"
  MYPY_BIN=".test-venv/bin/mypy"
  RUFF_BIN=".test-venv/bin/ruff"
else
  PYTHON_BIN="python3"
  MYPY_BIN="mypy"
  RUFF_BIN="ruff"
fi

status=0

run_gate() {
  local name="$1"
  shift
  echo "==> ${name}"
  if "$@"; then
    echo "PASS: ${name}"
  else
    echo "FAIL: ${name}"
    status=1
  fi
  echo
}

run_gate "pytest" "$PYTHON_BIN" -m pytest
run_gate "mypy" "$MYPY_BIN" src tests
run_gate "ruff check" "$RUFF_BIN" check .
run_gate "ruff format --check" "$RUFF_BIN" format --check .

if [[ "$status" -eq 0 ]]; then
  echo "SUMMARY: ALL LOCAL RELEASE CHECKS PASSED"
else
  echo "SUMMARY: ONE OR MORE LOCAL RELEASE CHECKS FAILED"
fi

exit "$status"
