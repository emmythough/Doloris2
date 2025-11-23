import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RENDER_URL = "https://doloris2.onrender.com" # Hardcoded from user input to be sure
WEBHOOK_URL = f"{RENDER_URL}/telegram/webhook"

def set_webhook():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
    payload = {"url": WEBHOOK_URL}
    
    print(f"Setting webhook to: {WEBHOOK_URL}")
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    set_webhook()
