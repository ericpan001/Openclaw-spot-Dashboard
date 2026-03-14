#!/usr/bin/env python3
"""
產生策略狀態資訊，供前端顯示
每分鐘呼叫更新
"""

import json
import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
STATUS_FILE = BASE_DIR / "status.json"
STRATEGY_V2_FILE = BASE_DIR / "strategy_v2.json"


def main():
    # 讀取 v2 策略設定
    with open(STRATEGY_V2_FILE) as f:
        strategy_v2 = json.load(f)

    trading_coins = [str(coin).upper().replace("USDT", "") for coin in strategy_v2.get("coins", [])]
    
    # 讀取現有 status
    status = {}
    if STATUS_FILE.exists():
        with open(STATUS_FILE) as f:
            status = json.load(f)
    
    # 更新策略資訊
    status["mode"] = "strategy-v2"
    status["watchlist"] = trading_coins
    status["strategy_v2"] = {
        "version": "趨勢回調 v2.0",
        "takeProfit": f"第一目標 +{strategy_v2.get('takeProfit', {}).get('firstTargetPct', 0.04) * 100:.1f}%賣出 50%，第二目標 +{strategy_v2.get('takeProfit', {}).get('secondTargetPct', 0.08) * 100:.1f}% 全賣",
        "stopLoss": f"固定{strategy_v2.get('stopLoss', {}).get('fixedLossPct', 0.015) * 100:.1f}% + 結構保護",
        "leverage": f"低波動{strategy_v2.get('position', {}).get('leverageVolatilityLow', {}).get('leverage', 10)}x / 中波動{strategy_v2.get('position', {}).get('leverageVolatilityMid', {}).get('leverage', 7)}x / 高波動{strategy_v2.get('position', {}).get('leverageVolatilityHigh', {}).get('leverage', 5)}x",
        "positionSize": f"單筆{strategy_v2.get('position', {}).get('sizeMinFraction', 0.10) * 100:.0f}%-{strategy_v2.get('position', {}).get('sizeMaxFraction', 0.15) * 100:.0f}%倉位，最多{strategy_v2.get('position', {}).get('maxConcurrentPositions', 3)}持倉",
        "entryLogic": "MA 趨勢判斷 + 4 選 3 回調開倉",
        "coins": trading_coins,
        "topN": strategy_v2.get("topN", 10)
    }
    
    # 保存
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)
    
    print(f"策略狀態已更新: {len(trading_coins)} 個交易幣種")


if __name__ == "__main__":
    main()
