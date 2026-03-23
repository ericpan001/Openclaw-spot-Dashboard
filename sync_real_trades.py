#!/usr/bin/env python3
import os, time, json, hmac, hashlib, urllib.request, urllib.parse, urllib.error
from pathlib import Path
from datetime import datetime, timezone, timedelta

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / '.env'
OUT = BASE_DIR / 'trades.json'
STATE = BASE_DIR / 'trade_sync_state.json'
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
TZ_TAIPEI = timezone(timedelta(hours=8))
KEEP_HOURS = 48
MAX_TRADES = 80

if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip().strip('"').strip("'")

API = os.getenv('BINANCE_API_KEY')
SEC = os.getenv('BINANCE_SECRET_KEY')


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def write_json(path: Path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def signed_get(path, params=None):
    params = params or {}
    params['timestamp'] = str(int(time.time() * 1000))
    params['recvWindow'] = '5000'
    q = urllib.parse.urlencode(params)
    sig = hmac.new(SEC.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = 'https://api.binance.com' + path + '?' + q + '&signature=' + sig
    req = urllib.request.Request(url, headers={'X-MBX-APIKEY': API, 'User-Agent': 'trade-sync'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def get_price(symbol):
    try:
        req = urllib.request.Request(
            f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}',
            headers={'User-Agent': 'trade-sync'}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return float(json.loads(r.read().decode())['price'])
    except Exception:
        return 0.0


def trade_key(t):
    base_id = t.get('orderId') or t.get('tradeId') or 0
    return f"{base_id}|{t.get('symbol')}|{t.get('type')}|{t.get('amount')}|{t.get('price')}|{t.get('reason','')}"


def sort_key(t):
    if t.get('orderId') is not None:
        return int(t.get('orderId', 0))
    if t.get('tradeId') is not None:
        return int(t.get('tradeId', 0))
    raw_time = str(t.get('time', ''))
    try:
        if len(raw_time) == 8 and raw_time.count(':') == 2:
            h, m, s = map(int, raw_time.split(':'))
            return h * 3600 + m * 60 + s
    except Exception:
        pass
    return 0


def is_recent_trade(t):
    try:
        raw_time = t.get('time', '')
        if len(raw_time) == 8 and raw_time.count(':') == 2:
            return True
        dt = datetime.strptime(raw_time, '%Y-%m-%d %H:%M:%S').replace(tzinfo=TZ_TAIPEI)
        age = datetime.now(TZ_TAIPEI) - dt
        return age.total_seconds() <= KEEP_HOURS * 3600
    except Exception:
        return True


def normalize_trade(raw, live_price):
    dt = datetime.fromtimestamp(raw['time'] / 1000, tz=timezone.utc).astimezone(TZ_TAIPEI)
    symbol = raw['symbol']
    side = '買入' if raw.get('isBuyer') else '賣出'
    qty = float(raw.get('qty', 0))
    price = float(raw.get('price', 0))
    pnl = 0.0 if raw.get('isBuyer') else max(0.0, (price - live_price) * qty) if live_price else 0.0
    return {
        'time': dt.strftime('%H:%M:%S'),
        'symbol': symbol.replace('USDT', ''),
        'type': side,
        'amount': qty,
        'price': price,
        'pnl': pnl,
        'reason': 'Binance 手動/真實成交同步',
        'tradeId': raw.get('id'),
        'orderId': raw.get('orderId'),
        'tradeAction': 'OPEN' if raw.get('isBuyer') else 'CLOSE',
        'syncSource': 'binance-myTrades',
        'isManualSync': True
    }


def aggregate_trades(trades):
    grouped = {}
    for t in trades:
        key = (t.get('orderId') or t.get('tradeId'), t.get('symbol'), t.get('type'), t.get('reason'))
        if key not in grouped:
            grouped[key] = dict(t)
            continue
        g = grouped[key]
        old_amt = float(g.get('amount', 0))
        new_amt = float(t.get('amount', 0))
        total_amt = old_amt + new_amt
        if total_amt > 0:
            g['price'] = ((float(g.get('price', 0)) * old_amt) + (float(t.get('price', 0)) * new_amt)) / total_amt
        g['amount'] = total_amt
        g['pnl'] = float(g.get('pnl', 0)) + float(t.get('pnl', 0))
        if int(t.get('tradeId') or 0) > int(g.get('tradeId') or 0):
            g['tradeId'] = t.get('tradeId')
            g['time'] = t.get('time')
    out = []
    for g in grouped.values():
        g['amount'] = round(float(g.get('amount', 0)), 4)
        g['price'] = round(float(g.get('price', 0)), 2)
        g['pnl'] = round(float(g.get('pnl', 0)), 4)
        out.append(g)
    return out


def sync_once():
    if not API or not SEC:
        return

    state = read_json(STATE, {})
    existing = read_json(OUT, [])
    merged = list(existing)
    changed = False

    for symbol in SYMBOLS:
        try:
            last_id = state.get(symbol, 0)
            params = {'symbol': symbol, 'limit': 20}
            if last_id:
                params['fromId'] = int(last_id) + 1
            trades = signed_get('/api/v3/myTrades', params) or []
            if not trades and not last_id:
                trades = signed_get('/api/v3/myTrades', {'symbol': symbol, 'limit': 10}) or []

            live_price = get_price(symbol)
            max_seen = last_id
            for raw in trades:
                max_seen = max(max_seen, int(raw.get('id', 0)))
                merged.append(normalize_trade(raw, live_price))
                changed = True
            state[symbol] = max_seen
        except urllib.error.HTTPError as e:
            print(f'sync {symbol} HTTP error: {e.code} {e.reason}')
        except Exception as e:
            print(f'sync {symbol} failed: {e}')

    merged = [t for t in merged if is_recent_trade(t)]
    merged = aggregate_trades(merged)
    # de-dup after aggregation
    dedup = {}
    for t in merged:
        dedup[trade_key(t)] = t
    merged = list(dedup.values())
    merged.sort(key=sort_key)
    merged = merged[-MAX_TRADES:]
    if changed:
        write_json(OUT, merged)
    write_json(STATE, state)


def main():
    if not API or not SEC:
        print('missing api key')
        return
    while True:
        sync_once()
        time.sleep(15)


if __name__ == '__main__':
    main()
