#!/usr/bin/env python3
import os, time, json, hmac, hashlib, urllib.request, urllib.parse, urllib.error
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV = BASE_DIR / '.env'
OUT = BASE_DIR / 'dashboard_assets.json'

if ENV.exists():
    for line in ENV.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip().strip('"').strip("'")

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


def write_error_payload(message):
    previous = {}
    try:
        previous = json.loads(OUT.read_text()) if OUT.exists() else {}
    except Exception:
        previous = {}
    payload = {
        'remainingUsdt': previous.get('remainingUsdt', 0.0),
        'investedValue': previous.get('investedValue', 0.0),
        'totalEquity': previous.get('totalEquity', 0.0),
        'holdings': previous.get('holdings', {}),
        'updatedAt': int(time.time() * 1000),
        'warning': message,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')


def main():
    if not API or not SEC:
        write_error_payload('missing api key')
        return

    try:
        acct = sget('/api/v3/account')
        balances = {b['asset']: float(b.get('free', 0)) + float(b.get('locked', 0)) for b in acct.get('balances', [])}

        usdt = balances.get('USDT', 0.0)
        watched = [('BTC', 'BTCUSDT'), ('ETH', 'ETHUSDT'), ('SOL', 'SOLUSDT')]

        holdings = {}
        invested = 0.0
        for asset, symbol in watched:
            qty = balances.get(asset, 0.0)
            try:
                price = pget(symbol)
            except Exception:
                price = 0.0
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
    except urllib.error.HTTPError as e:
        write_error_payload(f'HTTP {e.code}: {e.reason}')
    except urllib.error.URLError as e:
        write_error_payload(f'URL error: {e.reason}')
    except Exception as e:
        write_error_payload(f'update failed: {e}')


if __name__ == '__main__':
    main()
