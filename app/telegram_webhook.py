"""
Telegram Webhook Handler

Receives updates from Telegram, processes them via Adapter and Brain, and sends responses.
"""

from fastapi import APIRouter, Request, HTTPException
from app.channels.telegram_adapter import TelegramAdapter
from app.core.brain import get_brain
import logging
import traceback

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle incoming Telegram updates"""
    try:
        data = await request.json()
        logger.info(f"[WEBHOOK] ✅ Received data: {data}")
        
        adapter = TelegramAdapter()
        brain = get_brain()
        
        # 1. Process Update via Adapter
        logger.info("[WEBHOOK] 🔄 Processing update via TelegramAdapter...")
        user_id, text, file_url, file_metadata = await adapter.process_update(data)
        
        if not user_id:
            logger.warning("[WEBHOOK] ⚠️ No user_id found, ignoring update")
            return {"status": "ignored", "reason": "no_user_id"}
        
        logger.info(f"[WEBHOOK] ✅ Parsed: user_id={user_id}, text='{text}', file={file_url}")
        
        # 2. Pass to Brain
        logger.info(f"[WEBHOOK] 🧠 Sending to Brain for processing...")
        response_text = await brain.process_message(
            user_id=user_id,
            message=text,
            file_url=file_url,
            file_metadata=file_metadata
        )
        
        logger.info(f"[WEBHOOK] ✅ Brain returned: '{response_text[:100]}...'")
        
        # 3. Send Response via Adapter
        chat_id = data["message"]["chat"]["id"]
        logger.info(f"[WEBHOOK] 📤 Sending response to chat_id={chat_id}")
        await adapter.send_message(chat_id, response_text)
        
        logger.info("[WEBHOOK] ✅ Response sent successfully!")
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"[WEBHOOK] ❌ ERROR: {e}")
        logger.error(f"[WEBHOOK] ❌ Traceback: {traceback.format_exc()}")
        # Return 200 to prevent Telegram from retrying endlessly on logic errors
        return {"status": "error", "message": str(e)}
