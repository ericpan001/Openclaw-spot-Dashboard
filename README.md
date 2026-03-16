# 小龍蝦 24小時交易看盤 v3.0 PRO

這是一個針對 Binance **現貨（Spot）** 的極速交易看板專案，v3.0 引入了移動止盈與毫秒級同步技術。

---

## v3.0 PRO 更新亮點

- **移動止盈 (Trailing Stop)**：獲利達標後自動追蹤最高點，回落即自動平倉，鎖定最大利潤。
- **毫秒級價格跳動**：前端全面接取幣安 WebSocket 流，價格變動與交易所同步零延遲。
- **Telegram 實時推送**：內建通知模組，下單與策略判斷即時傳送至手機。
- **視覺化策略看板**：新增移動止盈進度條，清晰展示「最高獲利點」與「回落保護距離」。
- **趨勢敏感度優化**：調優 MA 斜率過濾器，更精準捕捉微小趨勢機會。

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
