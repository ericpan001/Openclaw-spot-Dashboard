#!/usr/bin/env python3
"""
OpenClaw 趨勢回調交易策略 v3.0.2 PRO
永續合約趨勢回調交易策略
"""

from __future__ import annotations
import argparse, hashlib, hmac, json, math, os, sys, time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent
BASE_URL = "https://api.binance.com"
USER_AGENT = "openclaw-trend-reversal/3.0.2"
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"
STATUS_FILE = BASE_DIR / "status.json"
TRADES_FILE = BASE_DIR / "trades.json"
THINKING_FILE = BASE_DIR / "thinking.json"
STRATEGY_V2_FILE = BASE_DIR / "strategy_v2.json"
POSITIONS_DB = BASE_DIR / "positions_v2.json"

def read_json(path: Path, default: Any) -> Any:
    try: return json.loads(path.read_text(encoding="utf-8"))
    except: return default

def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

@dataclass
class Config:
    version: str = "3.0.2-PRO"
    position_size_min: float = 0.25
    position_size_max: float = 0.35
    fixed_loss_pct: float = 0.015
    trailing_stop_activation_pct: float = 0.05
    trailing_stop_callback_pct: float = 0.015
    first_target_pct: float = 0.05
    time_exit_minutes: int = 1440
    volatility_min_pct: float = 0.05
    ma30_slope_min: float = 0.05

def load_env():
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

class BinanceClient:
    def __init__(self, api_key: str = "", secret_key: str = ""):
        self.api_key, self.secret_key, self.base_url = api_key, secret_key, BASE_URL
    def _sign(self, params: str) -> str:
        return hmac.new(self.secret_key.encode(), params.encode(), hashlib.sha256).hexdigest()
    def _request(self, endpoint: str, params: dict = None, signed: bool = False, method: str = 'GET') -> dict:
        url, query = f"{self.base_url}{endpoint}", ""
        if params:
            query = urlencode(params)
            if signed: query += f"&signature={self._sign(query)}"
        if method == 'GET' and query: url, data = f"{url}?{query}", None
        else: data = query.encode() if query else None
        req = Request(url, data=data, headers={"User-Agent": USER_AGENT, "X-MBX-APIKEY": self.api_key}, method=method)
        try:
            with urlopen(req, timeout=10) as resp: return json.loads(resp.read().decode())
        except Exception as e:
            if hasattr(e, 'read'): print(f"API Error: {e.read().decode()}")
            return {}
    def get_klines(self, symbol: str, interval: str = "1m", limit: int = 60) -> list:
        data = self._request("/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": limit}) or []
        return [{"high": float(k[2]), "low": float(k[3]), "close": float(k[4]), "open": float(k[1]), "volume": float(k[5])} for k in data]
    def place_order(self, symbol: str, side: str, order_type: str, quantity: float = None, price: float = None) -> dict:
        p = {"symbol": symbol, "side": side, "type": order_type, "timestamp": int(time.time() * 1000), "recvWindow": 5000}
        if quantity: p["quantity"] = quantity
        if price: p["price"], p["timeInForce"] = price, "GTC"
        if DRY_RUN: return {"orderId": 999, "status": "FILLED"}
        return self._request("/api/v3/order", p, signed=True, method='POST')

class TradingBot:
    def __init__(self, api_key: str, secret_key: str):
        self.client = BinanceClient(api_key, secret_key)
        self.config = Config()
        self.positions = read_json(POSITIONS_DB, {})
        self.trading_coins = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        self.last_events = []

    def add_thought(self, msg: str):
        thoughts = read_json(THINKING_FILE, [])
        thoughts.append({"time": datetime.now().strftime("%H:%M:%S"), "thought": msg})
        write_json(THINKING_FILE, thoughts[-100:])

    def append_trade(self, symbol, side, qty, price, pnl, reason):
        trades = read_json(TRADES_FILE, [])
        trades.append({"time": datetime.now().strftime("%H:%M:%S"), "type": side, "symbol": symbol.replace("USDT",""), "amount": round(qty, 4), "price": round(price, 2), "pnl": round(pnl, 4), "reason": reason})
        write_json(TRADES_FILE, trades[-50:])

    def get_equity(self):
        acc = self.client._request("/api/v3/account", {"timestamp": int(time.time()*1000)}, signed=True)
        bal = {b['asset']: float(b['free'])+float(b['locked']) for b in acc.get('balances', [])}
        eq = bal.get('USDT', 0.0)
        for a in ['BTC', 'ETH', 'SOL']:
            if bal.get(a, 0) > 0:
                p = self.client._request("/api/v3/ticker/price", {"symbol": f"{a}USDT"})
                eq += bal[a] * float(p.get('price', 0))
        return eq

    def check_positions(self):
        now = time.time()
        for symbol, pos in list(self.positions.items()):
            klines = self.client.get_klines(symbol, "1m", 1)
            if not klines: continue
            price = klines[-1]["close"]
            pnl = (price - pos["entry"]) / pos["entry"]
            pos["max_pnl"] = max(pos.get("max_pnl", 0), pnl)
            if pos["max_pnl"] >= self.config.trailing_stop_activation_pct:
                if (pos["max_pnl"] - pnl) >= self.config.trailing_stop_callback_pct:
                    self.close_pos(symbol, f"移動止盈回落 (高點:{pos['max_pnl']*100:.1f}%)")
            elif pnl <= -self.config.fixed_loss_pct:
                self.close_pos(symbol, "固定止損")

    def close_pos(self, symbol, reason):
        pos = self.positions.get(symbol)
        if not pos: return
        qty = float(pos["qty"])
        if "BTC" in symbol: qty = math.floor(qty * 100000) / 100000
        elif "ETH" in symbol: qty = math.floor(qty * 10000) / 10000
        res = self.client.place_order(symbol, "SELL", "MARKET", quantity=qty)
        if res.get("orderId") or res.get("status") == "FILLED":
            p = float(self.client.get_klines(symbol, "1m", 1)[-1]["close"])
            self.append_trade(symbol, "賣出", qty, p, (p-pos["entry"])*qty, reason)
            del self.positions[symbol]
            self.add_thought(f"🧾 {symbol} 平倉: {reason}")
            write_json(POSITIONS_DB, self.positions)

    def scan_and_trade(self):
        for symbol in self.trading_coins:
            if symbol in self.positions: continue
            klines = self.client.get_klines(symbol, "1m", 30)
            if len(klines) < 30: continue
            closes = [k["close"] for k in klines]
            ma30 = sum(closes)/30
            ma30_old = sum(closes[:-5])/30
            slope = (ma30 - ma30_old)/ma30_old * 100
            
            # 激進進場 4選2
            cond = []
            if abs(closes[-1] - ma30)/ma30*100 <= 1.2: cond.append("near_ma")
            if klines[-1]["close"] > klines[-1]["open"]: cond.append("bullish")
            if klines[-1]["volume"] < klines[-2]["volume"]: cond.append("vol_down")
            if closes[-1] > min([k["low"] for k in klines[-15:]]): cond.append("above_low")
            
            if slope >= self.config.ma30_slope_min and len(cond) >= 2:
                bal = self.get_equity()
                qty = (bal * self.config.position_size_min) / closes[-1]
                res = self.client.place_order(symbol, "BUY", "MARKET", quantity=round(qty, 5))
                if res.get("orderId"):
                    self.positions[symbol] = {"entry": closes[-1], "qty": qty, "open_time": time.time(), "max_pnl": 0}
                    self.append_trade(symbol, "買入", qty, closes[-1], 0, "趨勢進場")
                    self.add_thought(f"🎯 {symbol} 買入成功 (條件:{'/'.join(cond)})")
                    write_json(POSITIONS_DB, self.positions)

    def tick(self):
        self.add_thought(f"🔄 V2 掃描 {datetime.now().strftime('%H:%M:%S')}")
        self.check_positions()
        self.scan_and_trade()
        status = {"last_run": datetime.now().strftime("%H:%M:%S"), "balance": round(self.get_equity(), 2), "positions": len(self.positions)}
        write_json(STATUS_FILE, status)
        write_json(BASE_DIR / "dashboard_active_positions.json", {s: {"max_pnl": p["max_pnl"]} for s, p in self.positions.items()})

    def run(self):
        print("LOBSTER v3.0.2 PRO RUNNING")
        while True:
            try: self.tick(); time.sleep(30)
            except KeyboardInterrupt: break
            except Exception as e: print(f"Error: {e}"); time.sleep(30)

if __name__ == "__main__":
    load_env()
    api_key = os.getenv("BINANCE_API_KEY")
    secret_key = os.getenv("BINANCE_SECRET_KEY")
    if not api_key or not secret_key:
        print("Error: BINANCE_API_KEY or BINANCE_SECRET_KEY not found in .env")
        sys.exit(1)
    bot = TradingBot(api_key, secret_key)
    bot.run()
