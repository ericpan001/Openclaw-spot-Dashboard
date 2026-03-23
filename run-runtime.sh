#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

mkdir -p "$SCRIPT_DIR"

pkill -f "$SCRIPT_DIR/trade_v2.py" 2>/dev/null || true
pkill -f "$SCRIPT_DIR/update_dashboard_holdings.py" 2>/dev/null || true
pkill -f "$SCRIPT_DIR/update_dashboard_assets.py" 2>/dev/null || true
pkill -f "$SCRIPT_DIR/sync_real_trades.py" 2>/dev/null || true

nohup python3 "$SCRIPT_DIR/trade_v2.py" >> "$SCRIPT_DIR/live_trading.log" 2>&1 &
nohup python3 "$SCRIPT_DIR/update_dashboard_holdings.py" >> "$SCRIPT_DIR/dashboard_holdings.log" 2>&1 &
nohup sh -c 'while true; do python3 "$0/update_dashboard_assets.py"; sleep 5; done' "$SCRIPT_DIR" >> "$SCRIPT_DIR/dashboard_assets.log" 2>&1 &
nohup python3 "$SCRIPT_DIR/sync_real_trades.py" >> "$SCRIPT_DIR/trade_sync.log" 2>&1 &

echo "runtime started"
