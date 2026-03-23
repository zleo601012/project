#!/usr/bin/env bash
set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 not found; this repository requires Python 3.10+." >&2
  exit 1
fi

exec python3 "$(dirname "$0")/test_flow_services.py" "$@"
