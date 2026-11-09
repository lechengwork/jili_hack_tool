#!/usr/bin/env bash
# Launch only a fresh isolated capture server; obtain login URL before enabling VPN.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
exec "$ROOT/.venv/bin/python" -B -u games/545/capture_server.py
