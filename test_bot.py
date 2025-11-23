import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RENDER_URL = os.getenv("APP_BASE_URL", "https://doloris2.onrender.com")

def test_bot_info():
    """Test if the bot token is valid by fetching bot info"""
    print("1. Testing Bot Token Validity...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data.get("ok"):
            bot_info = data.get("result", {})
            print(f"   ✅ Bot is valid!")
            print(f"   Bot Name: {bot_info.get('first_name')}")
            print(f"   Username: @{bot_info.get('username')}")
            return True
        else:
            print(f"   ❌ Bot token is invalid: {data}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_webhook_info():
    """Check current webhook configuration"""
    print("\n2. Checking Webhook Configuration...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getWebhookInfo"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data.get("ok"):
            webhook_info = data.get("result", {})
            webhook_url = webhook_info.get("url", "")
            
            print(f"   Current Webhook: {webhook_url}")
            print(f"   Pending Updates: {webhook_info.get('pending_update_count', 0)}")
            
            if webhook_url == f"{RENDER_URL}/telegram/webhook":
                print(f"   ✅ Webhook is correctly set!")
                return True
            else:
                print(f"   ⚠️ Webhook mismatch. Expected: {RENDER_URL}/telegram/webhook")
                return False
        else:
            print(f"   ❌ Failed to get webhook info: {data}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_render_health():
    """Test if Render service is responding"""
    print("\n3. Testing Render Service Health...")
    url = f"{RENDER_URL}/health"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"   ✅ Render service is healthy!")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"   ❌ Render service returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error connecting to Render: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("DOLORIS 2 - TELEGRAM BOT TEST")
    print("=" * 50)
    
    bot_valid = test_bot_info()
    webhook_valid = test_webhook_info()
    render_healthy = test_render_health()
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Bot Token Valid:     {'✅' if bot_valid else '❌'}")
    print(f"Webhook Configured:  {'✅' if webhook_valid else '❌'}")
    print(f"Render Service:      {'✅' if render_healthy else '❌'}")
    
    if bot_valid and webhook_valid and render_healthy:
        print("\n🎉 All tests passed! Your bot is ready to use.")
        print(f"   Go to Telegram and message @{TELEGRAM_BOT_TOKEN.split(':')[0]}")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
