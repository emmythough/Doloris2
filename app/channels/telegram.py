import os
import logging
import httpx
from app.config import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

class TelegramClient:
    """
    Client for interacting with Telegram API.
    """
    
    BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    
    @staticmethod
    async def send_message(chat_id: str, text: str):
        """
        Send a text message to a chat.
        """
        if not TELEGRAM_BOT_TOKEN:
            logger.warning("TELEGRAM_BOT_TOKEN not set. Skipping message send.")
            return
            
        url = f"{TelegramClient.BASE_URL}/sendMessage"
        data = {
            "chat_id": int(chat_id),  # Telegram API requires integer, not string
            "text": text,
            "parse_mode": "Markdown"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=data)
                response.raise_for_status()
                logger.info(f"Sent Telegram message to {chat_id}")
            except Exception as e:
                logger.error(f"Failed to send Telegram message: {e}")
