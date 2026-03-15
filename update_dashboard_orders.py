#!/usr/bin/env python3
import os, time, json
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent
OUT = BASE_DIR / 'dashboard_orders.json'

def main():
    try:
        trades_file = BASE_DIR / 'trades.json'
        if not trades_file.exists():
            OUT.write_text(json.dumps({"orderCount": 0, "updatedAt": int(time.time()*1000)}))
            return

        trades_data = json.loads(trades_file.read_text())
        
        # 定義 24 小時前的時間點
        now = datetime.now()
        twenty_four_hours_ago = now - timedelta(hours=24)
        
        recent_count = 0
        for t in trades_data:
            time_str = t.get('time')
            if not time_str:
                continue
            
            try:
                # 轉換交易時間字串為 datetime 物件
                trade_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                # 只統計 24 小時內的開倉動作 (或是成交動作)
                if trade_time > twenty_four_hours_ago:
                    if t.get('tradeAction') == 'OPEN' or t.get('tradeAction') == 'CLOSE':
                        recent_count += 1
            except Exception:
                continue

        data = {
            "orderCount": recent_count,
            "updatedAt": int(time.time() * 1000)
        }
        
        OUT.write_text(json.dumps(data, indent=2))
        print(f"Updated 24h trade count: {recent_count}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
