import os
import logging
import httpx
from app.config import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

class TelegramClient:
    @staticmethod
    async def send_message(chat_id: int, text: str):
        """
        Sends a message to a Telegram user.
        """
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        
        # Ensure chat_id is an integer (Telegram API requirement)
        try:
            chat_id = int(chat_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid chat_id: {chat_id} (type: {type(chat_id)})")
            return

        logger.info(f"TelegramClient sending message to {chat_id} (Type: {type(chat_id)}) - VERSION 3.0.3 (Fixed)")
        
        data = {
            "chat_id": chat_id,
            "text": text
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=data)
                response.raise_for_status()
                logger.info(f"Sent Telegram message to {chat_id}")
            except Exception as e:
                logger.error(f"Failed to send Telegram message: {e}")
                # Re-raise so the worker knows it failed
                raise e
