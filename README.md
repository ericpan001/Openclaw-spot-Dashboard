# 小龍蝦 24小時交易看盤

這是一個針對 Binance **現貨（Spot）** 的本地交易看板專案，包含：

- 即時看板頁面（`index.html`）
- Spot 餘額 / 持倉 /買入均價 顯示
- OpenClaw 本機模型 / 版本顯示
- 策略狀態與思考流展示
- 本機 HTTP 看板服務

> 目前這個版本的定位是：**本地看盤 + 輔助決策 + 手動/半手動交易支援**。
> 並不是一個預設會自動替你連續下單的公開 SaaS 服務。

---

## 功能特色

- 繁體中文介面
- Binance Spot 帳戶讀取
- 顯示目前持倉、買入均價、目前市價
- 顯示 OpenClaw 目前模型、預設模型、版本、更新時間
- 支援本機區網存取
- 可搭配 OpenClaw / Telegram 使用

---

## 需求

- macOS / Linux
- Python 3.10+
- Binance API Key / Secret
- OpenClaw（若要顯示本機模型資訊）

---

## 安裝

### 1. 下載專案

```bash
git clone <YOUR_REPO_URL>
cd openclaw-trading-bot
```

### 2. 建立 `.env`

```bash
cp .env.example .env
```

填入你的 Binance API 憑證：

```env
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
```

---

## 啟動方式

### 啟動看板

```bash
./run-web.sh
```

預設會在：

```bash
http://127.0.0.1:8787
```

### 單次更新策略 / 狀態

```bash
python3 update_strategy_status.py
python3 update_dashboard_meta.py
python3 update_dashboard_holdings.py
python3 trade_v2.py run-once
```

### 持續執行 bot

```bash
./trade.sh
```

---

## 主要檔案

- `index.html`：前端看板
- `trade_v2.py`：主要策略 / 狀態更新
- `update_strategy_status.py`：策略狀態整理
- `update_dashboard_meta.py`：抓 OpenClaw 模型 / 版本資訊
- `update_dashboard_holdings.py`：抓 Spot 持倉 / 均價資訊
- `run-web.sh`：啟動本機看板服務
- `trade.sh`：啟動交易程式

---

## 注意事項

- `.env` 不會被提交到 Git
- 請勿把真實 API key / secret 上傳到 GitHub
- 若你要對外發佈，建議先確認是否要保留任何本機化設定
- 本專案涉及真實資產，請自行承擔交易風險

---

## 授權

如果你要公開釋出，建議你再補一個 LICENSE。
目前可先視為私人專案模板使用。
