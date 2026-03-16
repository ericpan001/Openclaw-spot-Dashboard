import os
import urllib.request
import urllib.parse

def send_telegram_msg(message):
    # 從環境變數或固定設定中獲取 Telegram Bot Token 和 Chat ID
    # 這裡預設讀取你的系統設定
    token = os.getenv("TELEGRAM_BOT_TOKEN", "7709852230:AAG23n-6n06EAsiH520N46C18jU_f40f0rY")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "6459383586")
    
    if not token or not chat_id:
        return
        
    try:
        msg = f"☁️ 小雲交易提醒：\n{message}"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": msg}).encode("utf-8")
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=10) as response:
            pass
    except Exception as e:
        print(f"Telegram 推送失敗: {e}")
