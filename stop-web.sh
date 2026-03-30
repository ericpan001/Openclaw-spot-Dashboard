#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
PID_FILE="web.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "Dashboard web is not running (no web.pid)"
  exit 0
fi

PID=$(cat "$PID_FILE" 2>/dev/null || true)
if [ -z "${PID:-}" ]; then
  echo "Invalid PID file, removing"
  rm -f "$PID_FILE"
  exit 0
fi

if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  sleep 1
  if kill -0 "$PID" 2>/dev/null; then
    echo "Process still alive, sending SIGKILL"
    kill -9 "$PID" 2>/dev/null || true
  fi
  echo "Dashboard web stopped (PID $PID)"
else
  echo "Process $PID not running, cleaning stale PID file"
fi
rm -f "$PID_FILE"
