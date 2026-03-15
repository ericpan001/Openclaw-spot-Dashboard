#!/usr/bin/env python3
import os
import time
import json
import hmac
import hashlib
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / '.env'
WINDOW_FILE = BASE_DIR / 'live_trading_window.json'
OUT_JSON = BASE_DIR / 'settlement_report_latest.json'
OUT_MD = BASE_DIR / 'settlement_report_latest.md'

for line in ENV_FILE.read_text().splitlines() if ENV_FILE.exists() else []:
    if '=' in line:
        k, v = line.split('=', 1)
        os.environ[k] = v

API = os.environ.get('BINANCE_API_KEY', '')
SEC = os.environ.get('BINANCE_SECRET_KEY', '')
START_CAPITAL = float(os.environ.get('START_CAPITAL_USDT', '99.979'))
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']


def signed_get(path, params=None):
    params = params or {}
    params['timestamp'] = str(int(time.time() * 1000))
    params['recvWindow'] = '5000'
    q = urllib.parse.urlencode(params)
    sig = hmac.new(SEC.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = 'https://api.binance.com' + path + '?' + q + '&signature=' + sig
    req = urllib.request.Request(url, headers={'X-MBX-APIKEY': API, 'User-Agent': 'settlement-report'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def public_get(path, params=None):
    q = ('?' + urllib.parse.urlencode(params)) if params else ''
    req = urllib.request.Request('https://api.binance.com' + path + q, headers={'User-Agent': 'settlement-report'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def load_window():
    if WINDOW_FILE.exists():
        try:
            data = json.loads(WINDOW_FILE.read_text())
            return int(data.get('startedAt', int(time.time()))), int(data.get('stopAt', int(time.time())))
        except Exception:
            pass
    now = int(time.time())
    return now, now


def main():
    now_ms = int(time.time() * 1000)
    started_at, stop_at = load_window()
    started_ms = started_at * 1000

    acct = signed_get('/api/v3/account') if API and SEC else {'balances': []}
    bal_map = {b['asset']: float(b.get('free', 0)) + float(b.get('locked', 0)) for b in acct.get('balances', [])}

    prices = {}
    for s in SYMBOLS:
        try:
            prices[s] = float(public_get('/api/v3/ticker/price', {'symbol': s})['price'])
        except Exception:
            prices[s] = 0.0

    usdt = bal_map.get('USDT', 0.0)
    btc_qty = bal_map.get('BTC', 0.0)
    eth_qty = bal_map.get('ETH', 0.0)
    sol_qty = bal_map.get('SOL', 0.0)

    holdings_value = {
        'BTC': btc_qty * prices.get('BTCUSDT', 0.0),
        'ETH': eth_qty * prices.get('ETHUSDT', 0.0),
        'SOL': sol_qty * prices.get('SOLUSDT', 0.0),
    }
    invested_value = sum(holdings_value.values())
    total_equity = usdt + invested_value
    total_pnl = total_equity - START_CAPITAL

    trades_window = []
    distinct_orders = set()
    raw_rows = 0
    for s in SYMBOLS:
        try:
            rows = signed_get('/api/v3/myTrades', {'symbol': s, 'limit': '1000'}) if API and SEC else []
        except Exception:
            rows = []
        for t in rows:
            t_ms = int(t.get('time', 0) or 0)
            if t_ms >= started_ms:
                trades_window.append(t)
                raw_rows += 1
                if t.get('orderId') is not None:
                    distinct_orders.add(t.get('orderId'))

    payload = {
        'generatedAt': now_ms,
        'window': {
            'startedAt': started_at,
            'stopAt': stop_at,
            'startedAtText': datetime.fromtimestamp(started_at).strftime('%Y-%m-%d %H:%M:%S'),
            'generatedAtText': datetime.fromtimestamp(now_ms / 1000).strftime('%Y-%m-%d %H:%M:%S'),
        },
        'capital': {
            'startCapitalUsdt': START_CAPITAL,
            'remainingUsdt': usdt,
            'investedValue': invested_value,
            'totalEquity': total_equity,
            'totalPnl': total_pnl,
        },
        'holdings': {
            'BTC': {'qty': btc_qty, 'price': prices.get('BTCUSDT', 0.0), 'value': holdings_value['BTC']},
            'ETH': {'qty': eth_qty, 'price': prices.get('ETHUSDT', 0.0), 'value': holdings_value['ETH']},
            'SOL': {'qty': sol_qty, 'price': prices.get('SOLUSDT', 0.0), 'value': holdings_value['SOL']},
        },
        'tradesDuringWindow': {
            'rawRows': raw_rows,
            'orderCount': len(distinct_orders),
        }
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')

    md = []
    md.append('# Settlement Report (48h)')
    md.append('')
    md.append(f"- Generated: {payload['window']['generatedAtText']}")
    md.append(f"- Window start: {payload['window']['startedAtText']}")
    md.append('')
    md.append('## Capital')
    md.append(f"- Start capital: {START_CAPITAL:.4f} USDT")
    md.append(f"- Remaining USDT: {usdt:.4f}")
    md.append(f"- Invested value: {invested_value:.4f}")
    md.append(f"- Total equity: {total_equity:.4f}")
    md.append(f"- Total PnL: {total_pnl:+.4f} USDT")
    md.append('')
    md.append('## Holdings')
    md.append(f"- BTC: qty={btc_qty:.8f}, price={prices.get('BTCUSDT', 0.0):.2f}, value={holdings_value['BTC']:.4f}")
    md.append(f"- ETH: qty={eth_qty:.8f}, price={prices.get('ETHUSDT', 0.0):.2f}, value={holdings_value['ETH']:.4f}")
    md.append(f"- SOL: qty={sol_qty:.8f}, price={prices.get('SOLUSDT', 0.0):.2f}, value={holdings_value['SOL']:.4f}")
    md.append('')
    md.append('## Trades during window')
    md.append(f"- Raw rows: {raw_rows}")
    md.append(f"- Distinct order count: {len(distinct_orders)}")

    OUT_MD.write_text('\n'.join(md) + '\n')
    print('Settlement report generated:', OUT_JSON)


if __name__ == '__main__':
    main()
