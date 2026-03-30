#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
PORT="${PORT:-1688}"
PID_FILE="web.pid"
LOG_FILE="web.log"

if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE" 2>/dev/null || true)
  if [ -n "${PID:-}" ] && kill -0 "$PID" 2>/dev/null; then
    echo "Dashboard web is RUNNING"
    echo "PID: $PID"
    echo "URL: http://127.0.0.1:$PORT"
    [ -f "$LOG_FILE" ] && echo "Log: $SCRIPT_DIR/$LOG_FILE"
    exit 0
  fi
fi

echo "Dashboard web is NOT running"
[ -f "$LOG_FILE" ] && echo "Last log: $SCRIPT_DIR/$LOG_FILE"
exit 1
