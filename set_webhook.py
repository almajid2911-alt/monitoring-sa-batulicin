import sys
import requests

def set_webhook(bot_token, webhook_url):
    url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    payload = {"url": webhook_url}
    
    print(f"Mengirim permintaan setWebhook ke: {url}")
    print(f"Target URL: {webhook_url}")
    
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        if data.get("ok"):
            print("✅ Webhook berhasil diatur!")
        else:
            print("❌ Gagal mengatur webhook:")
            print(data)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Penggunaan: python set_webhook.py <BOT_TOKEN> <WEBHOOK_URL>")
        print("Contoh: python set_webhook.py 123456:ABC-DEF https://monitoring.internetbisnis.biz.id/api/telegram/webhook")
        sys.exit(1)
        
    set_webhook(sys.argv[1], sys.argv[2])
