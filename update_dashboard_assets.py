#!/usr/bin/env python3
import os, time, json, hmac, hashlib, urllib.request, urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV = BASE_DIR / '.env'
OUT = BASE_DIR / 'dashboard_assets.json'

for line in ENV.read_text().splitlines():
    if '=' in line:
        k, v = line.split('=', 1)
        os.environ[k] = v

API = os.environ.get('BINANCE_API_KEY', '')
SEC = os.environ.get('BINANCE_SECRET_KEY', '')


def sget(path, params=None):
    params = params or {}
    params['timestamp'] = str(int(time.time() * 1000))
    params['recvWindow'] = '5000'
    q = urllib.parse.urlencode(params)
    sig = hmac.new(SEC.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = 'https://api.binance.com' + path + '?' + q + '&signature=' + sig
    req = urllib.request.Request(url, headers={'X-MBX-APIKEY': API, 'User-Agent': 'dashboard-assets'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def pget(symbol):
    req = urllib.request.Request('https://api.binance.com/api/v3/ticker/price?symbol=' + symbol, headers={'User-Agent': 'dashboard-assets'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return float(json.loads(r.read().decode())['price'])


def main():
    if not API or not SEC:
        OUT.write_text(json.dumps({'error': 'missing api key'}, ensure_ascii=False, indent=2) + '\n')
        return

    acct = sget('/api/v3/account')
    balances = {b['asset']: float(b.get('free', 0)) + float(b.get('locked', 0)) for b in acct.get('balances', [])}

    usdt = balances.get('USDT', 0.0)
    watched = [('BTC', 'BTCUSDT'), ('ETH', 'ETHUSDT'), ('SOL', 'SOLUSDT')]

    holdings = {}
    invested = 0.0
    for asset, symbol in watched:
        qty = balances.get(asset, 0.0)
        price = pget(symbol)
        value = qty * price
        holdings[asset] = {
            'qty': qty,
            'price': price,
            'value': value,
        }
        invested += value

    payload = {
        'remainingUsdt': usdt,
        'investedValue': invested,
        'totalEquity': usdt + invested,
        'holdings': holdings,
        'updatedAt': int(time.time() * 1000),
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
