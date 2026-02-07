#!/usr/bin/env bash
set -euo pipefail

poetry build

echo "Build artifacts:"
ls -la dist
