#!/usr/bin/env python3
import os
import time
import json
import hmac
import hashlib
import urllib.request
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / '.env'
OUT = BASE_DIR / 'dashboard_holdings.json'

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
    req = urllib.request.Request(url, headers={'X-MBX-APIKEY': API, 'User-Agent': 'dashboard-holdings'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def weighted_avg_buy_price(trades):
    buy_trades = [t for t in trades if t.get('isBuyer')]
    qty_sum = sum(float(t['qty']) for t in buy_trades)
    quote_sum = sum(float(t['quoteQty']) for t in buy_trades)
    if qty_sum <= 0:
        return None
    return quote_sum / qty_sum


def main():
    acct = signed_get('/api/v3/account')
    balances = {b['asset']: float(b['free']) + float(b['locked']) for b in acct.get('balances', [])}
    result = {'holdings': [], 'updatedAt': int(time.time() * 1000)}
    for asset in ['BTC', 'ETH', 'BNB', 'SOL', 'XRP']:
        qty = balances.get(asset, 0.0)
        if qty <= 0:
            continue
        symbol = asset + 'USDT'
        trades = signed_get('/api/v3/myTrades', {'symbol': symbol, 'limit': '50'})
        avg = weighted_avg_buy_price(trades)
        result['holdings'].append({
            'asset': asset,
            'symbol': symbol,
            'quantity': qty,
            'avgBuyPrice': avg
        })
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
