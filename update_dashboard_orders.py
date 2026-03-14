#!/usr/bin/env python3
import os, time, json, hmac, hashlib, urllib.request, urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / '.env'
OUT = BASE_DIR / 'dashboard_orders.json'

for line in ENV_FILE.read_text().splitlines():
    if '=' in line:
        k, v = line.split('=', 1)
        os.environ[k] = v

API = os.environ['BINANCE_API_KEY']
SEC = os.environ['BINANCE_SECRET_KEY']


def signed_get(path, params=None):
    params = params or {}
    params['timestamp'] = str(int(time.time() * 1000))
    params['recvWindow'] = '5000'
    q = urllib.parse.urlencode(params)
    sig = hmac.new(SEC.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = 'https://api.binance.com' + path + '?' + q + '&signature=' + sig
    req = urllib.request.Request(url, headers={'X-MBX-APIKEY': API, 'User-Agent': 'dashboard-orders'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def main():
    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'BNBUSDT']
    rows = []
    order_ids = set()
    by_symbol = {}
    for symbol in symbols:
        try:
            trades = signed_get('/api/v3/myTrades', {'symbol': symbol, 'limit': '100'})
        except Exception:
            trades = []
        rows.extend(trades)
        ids = sorted({t.get('orderId') for t in trades if t.get('orderId') is not None})
        by_symbol[symbol] = len(ids)
        order_ids.update(ids)
    payload = {
        'rawTradeRows': len(rows),
        'orderCount': len(order_ids),
        'bySymbol': by_symbol,
        'updatedAt': int(time.time() * 1000)
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
