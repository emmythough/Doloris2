"""
Telegram Webhook Handler

Receives updates from Telegram, processes them via Adapter and Brain, and sends responses.
"""

from fastapi import APIRouter, Request, HTTPException
from app.channels.telegram_adapter import TelegramAdapter
from app.core.brain import get_brain
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle incoming Telegram updates"""
    try:
        data = await request.json()
        logger.info(f"Received webhook data: {data}")
        
        adapter = TelegramAdapter()
        brain = get_brain()
        
        # 1. Process Update via Adapter
        # Returns: user_id, text, file_url, file_metadata
        user_id, text, file_url, file_metadata = await adapter.process_update(data)
        
        if not user_id:
            return {"status": "ignored", "reason": "no_user_id"}
            
        logger.info(f"Processing message from {user_id}: {text} (File: {file_url})")
        
        # 2. Pass to Brain
        response_text = await brain.process_message(
            user_id=user_id,
            message=text,
            file_url=file_url,
            file_metadata=file_metadata
        )
        
        # 3. Send Response via Adapter
        await adapter.send_message(data["message"]["chat"]["id"], response_text)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        # Return 200 to prevent Telegram from retrying endlessly on logic errors
        return {"status": "error", "message": str(e)}
