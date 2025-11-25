"""
Telegram Webhook Handler

Receives updates from Telegram, processes them via Adapter and Brain, and sends responses.
"""

from fastapi import APIRouter, Request, HTTPException
from app.channels.telegram_adapter import TelegramAdapter
from app.core.brain import get_brain
import logging
import traceback
import json
import time

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle incoming Telegram updates"""
    start_time = time.time()
    request_id = f"req_{int(start_time * 1000)}"
    
    logger.info(f"[WEBHOOK:{request_id}] ====== NEW REQUEST ======")
    
    try:
        # Get raw payload
        data = await request.json()
        
        # Log full payload for debugging
        logger.info(f"[WEBHOOK:{request_id}] 📥 RAW TELEGRAM PAYLOAD:")
        logger.info(f"[WEBHOOK:{request_id}] {json.dumps(data, indent=2)}")
        
        # Extract message info for logging
        message_info = {
            "update_id": data.get("update_id"),
            "message_id": data.get("message", {}).get("message_id"),
            "chat_id": data.get("message", {}).get("chat", {}).get("id"),
            "from_id": data.get("message", {}).get("from", {}).get("id"),
            "from_username": data.get("message", {}).get("from", {}).get("username"),
            "text": data.get("message", {}).get("text", "")[:100],
            "has_document": "document" in data.get("message", {}),
            "has_photo": "photo" in data.get("message", {}),
        }
        logger.info(f"[WEBHOOK:{request_id}] 📋 MESSAGE INFO: {json.dumps(message_info, indent=2)}")
        
        adapter = TelegramAdapter()
        brain = get_brain()
        
        # 1. Process Update via Adapter
        logger.info(f"[WEBHOOK:{request_id}] 🔄 STEP 1/4: Processing update via TelegramAdapter...")
        process_start = time.time()
        
        user_id, text, file_url, file_metadata = await adapter.process_update(data)
        
        process_duration = time.time() - process_start
        logger.info(f"[WEBHOOK:{request_id}] ⏱️ Adapter processing took {process_duration:.2f}s")
        
        if not user_id:
            logger.warning(f"[WEBHOOK:{request_id}] ⚠️ No user_id found, ignoring update")
            logger.warning(f"[WEBHOOK:{request_id}] ⚠️ RAW DATA: {json.dumps(data, indent=2)}")
            return {"status": "ignored", "reason": "no_user_id"}
        
        logger.info(f"[WEBHOOK:{request_id}] ✅ PARSED RESULT:")
        logger.info(f"[WEBHOOK:{request_id}]   - user_id: {user_id}")
        logger.info(f"[WEBHOOK:{request_id}]   - text: '{text}'")
        logger.info(f"[WEBHOOK:{request_id}]   - file_url: {file_url}")
        logger.info(f"[WEBHOOK:{request_id}]   - file_metadata: {file_metadata}")
        
        # 2. Pass to Brain
        logger.info(f"[WEBHOOK:{request_id}] 🧠 STEP 2/4: Sending to Brain for processing...")
        brain_start = time.time()
        
        response_text = await brain.process_message(
            user_id=user_id,
            message=text,
            file_url=file_url,
            file_metadata=file_metadata
        )
        
        brain_duration = time.time() - brain_start
        logger.info(f"[WEBHOOK:{request_id}] ⏱️ Brain processing took {brain_duration:.2f}s")
        logger.info(f"[WEBHOOK:{request_id}] ✅ Brain returned ({len(response_text)} chars): '{response_text[:200]}...'")
        
        # 3. Send Response via Adapter
        chat_id = data.get("message", {}).get("chat", {}).get("id")
        if not chat_id:
            logger.error(f"[WEBHOOK:{request_id}] ❌ No chat_id found in payload!")
            return {"status": "error", "message": "no_chat_id"}
        
        logger.info(f"[WEBHOOK:{request_id}] 📤 STEP 3/4: Sending response to chat_id={chat_id}")
        
        # CRITICAL SAFETY CHECK: Never send empty messages to Telegram
        if not response_text or not response_text.strip():
            logger.error(f"[WEBHOOK:{request_id}] ❌ Brain returned empty response!")
            logger.error(f"[WEBHOOK:{request_id}] ❌ This is a bug - using fallback message")
            response_text = "I processed your message, but I'm having trouble formulating a response. Could you try rephrasing that?"
        
        send_start = time.time()
        
        send_result = await adapter.send_message(chat_id, response_text)
        
        send_duration = time.time() - send_start
        logger.info(f"[WEBHOOK:{request_id}] ⏱️ Message send took {send_duration:.2f}s")
        logger.info(f"[WEBHOOK:{request_id}] 📤 Send result: {send_result}")
        
        # 4. Complete
        total_duration = time.time() - start_time
        logger.info(f"[WEBHOOK:{request_id}] ✅ STEP 4/4: COMPLETE!")
        logger.info(f"[WEBHOOK:{request_id}] ⏱️ TOTAL TIME: {total_duration:.2f}s")
        logger.info(f"[WEBHOOK:{request_id}] ====== REQUEST COMPLETE ======")
        
        return {"status": "ok", "request_id": request_id, "duration": total_duration}
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"[WEBHOOK:{request_id}] ❌ ====== ERROR ======")
        logger.error(f"[WEBHOOK:{request_id}] ❌ ERROR TYPE: {type(e).__name__}")
        logger.error(f"[WEBHOOK:{request_id}] ❌ ERROR MESSAGE: {str(e)}")
        logger.error(f"[WEBHOOK:{request_id}] ❌ FULL TRACEBACK:")
        logger.error(traceback.format_exc())
        logger.error(f"[WEBHOOK:{request_id}] ❌ Duration before error: {duration:.2f}s")
        logger.error(f"[WEBHOOK:{request_id}] ====== ERROR END ======")
        
        # Return 200 to prevent Telegram from retrying endlessly on logic errors
        return {"status": "error", "message": str(e), "type": type(e).__name__, "request_id": request_id}
