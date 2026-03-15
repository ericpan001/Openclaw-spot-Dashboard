#!/usr/bin/env python3
import os, time, json, hmac, hashlib, urllib.request, urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / '.env'
OUT = BASE_DIR / 'dashboard_holdings.json'

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
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())

def get_avg_price(symbol):
    try:
        trades = signed_get('/api/v3/myTrades', {'symbol': symbol, 'limit': 20})
        for t in reversed(trades or []):
            if t.get('isBuyer'): return float(t['price'])
        return 0.0
    except: return 0.0

def main():
    if not API or not SEC: return
    while True: # 讓它變成持續監控模式
        try:
            acc = signed_get('/api/v3/account')
            holdings = []
            for b in acc.get('balances', []):
                total = float(b.get('free', 0)) + float(b.get('locked', 0))
                # 只要價值超過約 1 USDT 就算持倉，確保自動買入的幣 (如 SOL) 立即被發現
                if total > 0:
                    asset = b['asset']
                    if asset == 'USDT' or asset.startswith('LD'): continue # 排除現金和理財
                    
                    symbol = f"{asset}USDT"
                    # 只有真的有數量的才去抓成本，省 API
                    if total > 0.0001: 
                        avg_price = get_avg_price(symbol)
                        holdings.append({
                            "asset": asset,
                            "symbol": symbol,
                            "quantity": total,
                            "avgBuyPrice": avg_price
                        })
            
            OUT.write_text(json.dumps({"holdings": holdings, "updatedAt": int(time.time()*1000)}, indent=2))
            # print(f"Holdings updated: {[h['asset'] for h in holdings]}")
        except Exception as e:
            print(f"Update error: {e}")
        time.sleep(5) # 每 5 秒掃描一次帳戶，極速同步

if __name__ == "__main__":
    main()
