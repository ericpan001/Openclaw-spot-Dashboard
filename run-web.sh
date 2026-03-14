#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
PORT="${PORT:-8787}"
exec python3 -m http.server "$PORT" --bind 0.0.0.0
