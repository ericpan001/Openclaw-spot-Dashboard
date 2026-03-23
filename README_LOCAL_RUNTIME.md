# Local runtime files

These files are generated locally at runtime and are intentionally excluded from GitHub:

- `.env`
- `status.json`
- `thinking.json`
- `trades.json`
- `dashboard_*.json`
- `positions_v2.json`
- `trade_sync_state.json`
- `*.log`
- `*.pid`

They are recreated automatically by the dashboard / trading runtime.

## Runtime helpers

- `sync_real_trades.py` continuously syncs real Binance fills (including manual spot trades) into `trades.json`.
- `update_dashboard_holdings.py` syncs holdings snapshots.
- `update_dashboard_assets.py` syncs equity and asset values.
- `run-runtime.sh` starts the full local runtime: trading bot, holdings sync, assets sync, and real trade sync.

## Trades display

- Real Binance manual fills are tagged as `手動同步` in the dashboard.
- Strategy-generated trades remain tagged as `策略`.
- Trade sync keeps only the recent window (48h / max 80 rows) so `trades.json` stays readable.
