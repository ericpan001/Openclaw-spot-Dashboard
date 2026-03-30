#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
PORT="${PORT:-1688}"
PID_FILE="web.pid"
LOG_FILE="web.log"

cleanup_stale_listener() {
  python3 - "$PORT" <<'PY'
import subprocess, re, os, signal, sys
port = sys.argv[1]
ps = subprocess.check_output(['ps','-ax','-o','pid=,command='], text=True)
found = []
for line in ps.splitlines():
    if f'http.server {port}' in line:
        m = re.match(r'\s*(\d+)\s+(.*)', line)
        if m:
            found.append((int(m.group(1)), m.group(2)))
for pid, cmd in found:
    try:
        os.kill(pid, signal.SIGTERM)
        print(f'Cleaned stale listener PID {pid}: {cmd}')
    except ProcessLookupError:
        pass
PY
}

if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE" 2>/dev/null || true)
  if [ -n "${PID:-}" ] && kill -0 "$PID" 2>/dev/null; then
    echo "Dashboard web already running (PID $PID) on port $PORT"
    exit 0
  else
    rm -f "$PID_FILE"
  fi
fi

cleanup_stale_listener || true
sleep 1

nohup python3 -m http.server "$PORT" --bind 0.0.0.0 > "$LOG_FILE" 2>&1 &
PID=$!
echo "$PID" > "$PID_FILE"
sleep 1
if kill -0 "$PID" 2>/dev/null; then
  echo "Dashboard web started (PID $PID) on http://127.0.0.1:$PORT"
else
  echo "Failed to start dashboard web. Check $LOG_FILE"
  rm -f "$PID_FILE"
  exit 1
fi
