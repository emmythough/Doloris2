"""
Quick diagnostic script to test Telegram API directly.
Run this locally to see the exact error from Telegram.
"""
import asyncio
import httpx
import logging
import os

# Get credentials from environment or use defaults
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8056668190:AAGTRIDB7Y6tZKIXSRfsTx6YSsG_TTeO3b8")
CHAT_ID = 605546234

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_telegram():
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    # Test with a simple message
    test_message = "Hello from diagnostic script! 👋"
    
    data = {
        "chat_id": CHAT_ID,
        "text": test_message
    }
    
    logger.info(f"Testing Telegram API...")
    logger.info(f"URL: {url}")
    logger.info(f"Payload: {data}")
    logger.info(f"Chat ID type: {type(CHAT_ID)}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data)
            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Response Body: {response.text}")
            
            if response.status_code == 200:
                logger.info("✅ SUCCESS! Message sent successfully!")
            else:
                logger.error(f"❌ FAILED with status {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("TELEGRAM API DIAGNOSTIC TEST")
    print("=" * 60)
    asyncio.run(test_telegram())
