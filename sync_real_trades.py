#!/usr/bin/env python3
import os, time, json, hmac, hashlib, urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime, timezone, timedelta

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / '.env'
OUT = BASE_DIR / 'trades.json'

if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k.strip()] = v.strip().strip('"').strip("'")

API = os.getenv('BINANCE_API_KEY')
SEC = os.getenv('BINANCE_SECRET_KEY')

def signed_get(path, params=None):
    params = params or {}
    params['timestamp'] = str(int(time.time() * 1000))
    params['recvWindow'] = '5000'
    q = urllib.parse.urlencode(params)
    sig = hmac.new(SEC.encode(), q.encode(), hashlib.sha256).hexdigest()
    url = 'https://api.binance.com' + path + '?' + q + '&signature=' + sig
    req = urllib.request.Request(url, headers={'X-MBX-APIKEY': API})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())

def get_live_price(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        with urllib.request.urlopen(url, timeout=5) as r:
            return float(json.loads(r.read().decode())['price'])
    except: return 0.0

def main():
    if not API or not SEC: return
    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
    all_trades = []
    
    # 台北時間偏移
    tz_taipei = timezone(timedelta(hours=8))
    
    for symbol in symbols:
        try:
            live_price = get_live_price(symbol)
            trades = signed_get('/api/v3/myTrades', {'symbol': symbol, 'limit': 5})
            if trades:
                # 取得該幣種最後一筆成交
                t = trades[-1]
                # 轉換幣安時間戳 (UTC) 到台北時間
                dt = datetime.fromtimestamp(t['time']/1000, tz=timezone.utc).astimezone(tz_taipei)
                
                price = float(t['price'])
                qty = float(t['qty'])
                # 計算即時盈虧 (現價 - 成交價) * 數量
                pnl = (live_price - price) * qty if t['isBuyer'] else 0.0
                
                all_trades.append({
                    "time": dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "symbol": symbol,
                    "type": "BUY" if t['isBuyer'] else "SELL",
                    "price": price,
                    "amount": qty,
                    "pnl": pnl
                })
        except: continue
    
    all_trades.sort(key=lambda x: x['time'], reverse=True)
    OUT.write_text(json.dumps(all_trades, indent=2))
    print(f"Synced {len(all_trades)} trades with real time and PnL.")

if __name__ == "__main__":
    main()
