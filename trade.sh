#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

if pgrep -f "$SCRIPT_DIR/trade_v2.py run" >/dev/null 2>&1; then
  exit 0
fi

exec python3 "$SCRIPT_DIR/trade_v2.py" run "$@"
