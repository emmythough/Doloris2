import os
import logging
import httpx
from app.config import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

class TelegramClient:
    """
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=data)
                response.raise_for_status()
                logger.info(f"Sent Telegram message to {chat_id}")
            except Exception as e:
                logger.error(f"Failed to send Telegram message: {e}")
