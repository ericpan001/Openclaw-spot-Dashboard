# 🦞 小龍蝦 24小時交易看盤 v3.0.2 PRO

這是一個針對 Binance **現貨（Spot）** 的極速交易看板專案，v3.0.2 版本進行了深度的策略優化與穩定性修復，讓你在手機與電腦端都能享受到極致的自動化交易體驗。

---

## 🚀 v3.0.2 PRO 更新亮點

- **真·移動止盈鎖定**：修復前端顯示高點會隨價格下跌的問題，改用 `LocalStorage` 進行強記憶鎖定，確保「回落距離」精準無誤。
- **大波段策略優化**：
  - **5% 啟動門檻**：獲利達 5% 正式開啟移動止盈。
  - **1.5% 回落保護**：給予幣價更多呼吸空間，避開假跌破洗盤。
  - **24小時抱單**：取消原本的 30 分鐘強制平倉限制，擁抱完整趨勢。
- **激進進場邏輯 (4選2)**：大幅降低進場門檻，在強勢趨勢中更主動地部署資金。
- **自動化持倉接管**：只要帳戶內有 BTC/ETH/SOL，機器人一開機便會自動「領養」並納入移動止盈監控範圍。
- **30% 重倉模式**：預設單筆投入資金比例調高至 30%，最大化資金利用率。

---

## 💎 主要特色

- **純本地化存儲**：敏感資料（API Key/Secret）僅保存在你的本地伺服器，不經過任何第三方雲端。
- **毫秒級價格跳動**：前端直連幣安 WebSocket，實現真正的零延遲看盤。
- **全自動記帳**：每一筆平倉原因與盈虧自動記錄，隨時追蹤績效。
- **跨平台一致性**：優化手機瀏覽器適配，讓你在捷運上也能隨時監控機器人思考流。

---

## 功能特色

- 繁體中文介面
- Binance Spot 帳戶實時讀取
- 顯示即時持倉、買入均價、目前市價、未實現損益
- 顯示 OpenClaw 模型資訊與 AI 思考流
- 支援本機區網存取與 Cloudflare Tunnel 遠端看盤

---

## 需求

- macOS / Linux / Windows (WSL)
- Python 3.9+
- Binance API Key / Secret (需開啟讀取與交易權限)

---

## 安裝與啟動

### 1. 下載專案

```bash
git clone https://github.com/ericpan001/Openclaw-spot-Dashboard.git
cd Openclaw-spot-Dashboard
```

### 2. 設定環境變數

建立 `.env` 檔案並填入憑證：

```env
BINANCE_API_KEY=你的API_KEY
BINANCE_SECRET_KEY=你的SECRET_KEY
```

### 3. 啟動服務

**開啟網頁服務：**
```bash
./run-web.sh
```

**開啟背景數據同步與交易監控：**
```bash
python3 update_dashboard_holdings.py &
python3 sync_real_trades.py &
python3 trade_v2.py run
```

---

## 安全建議

- **不要直接把此看板暴露到公網**：建議配合 Cloudflare Tunnel 或 VPN 使用。
- **API 安全**：請務必在幣安後台開啟 **IP 白名單限制**，僅允許你的伺服器/主機存取。
- **不要上傳 .env**：專案已預設 `.gitignore` 排除環境變數檔，請勿移除。

---

## 主要組件

- `index.html`：即時看盤前端（支援直連幣安 API）
- `trade_v2.py`：核心交易策略與思考流產出
- `sync_real_trades.py`：真實成交紀錄同步工具
- `update_dashboard_holdings.py`：資產與持倉即時同步工具

---

## 注意事項

- 本專案涉及真實資產，策略僅供參考，請自行承擔交易風險。
- 專案由 OpenClaw 小雲輔助開發。

---

## 授權

私人專案模板，建議僅供學習與個人交易輔助使用。
