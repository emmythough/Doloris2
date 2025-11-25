"""
Diagnostic Endpoint - Test message flow without Telegram

This endpoint simulates Telegram webhook payloads for testing.
"""

from fastapi import APIRouter
from app.channels.telegram_adapter import TelegramAdapter
from app.core.brain import get_brain
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/test-message")
async def test_message(user_id: int, text: str = "Hello Doloris!"):
    """
    Test the message flow without actually using Telegram
    
    Args:
        user_id: Telegram user ID to simulate
        text: Message text to send
    
    Example:
        POST /diagnostic/test-message?user_id=123456789&text=Hello
    """
    
    logger.info(f"[DIAGNOSTIC] Testing message flow for user_id={user_id}")
    
    try:
        brain = get_brain()
        
        response_text = await brain.process_message(
            user_id=user_id,
            message=text,
            file_url=None,
            file_metadata=None
        )
        
        return {
            "status": "success",
            "user_id": user_id,
            "input_text": text,
            "response_text": response_text,
            "response_length": len(response_text)
        }
        
    except Exception as e:
        logger.error(f"[DIAGNOSTIC] Error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }

@router.post("/test-webhook")
async def test_webhook():
    """
    Test with a sample Telegram webhook payload
    """
    
    sample_payload = {
        "update_id": 999999999,
        "message": {
            "message_id": 123,
            "from": {
                "id": 123456789,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser",
                "language_code": "en"
            },
            "chat": {
                "id": 123456789,
                "first_name": "Test",
                "username": "testuser",
                "type": "private"
            },
            "date": 1234567890,
            "text": "Hello Doloris! This is a test message."
        }
    }
    
    logger.info("[DIAGNOSTIC] Testing with sample webhook payload")
    
    try:
        adapter = TelegramAdapter()
        brain = get_brain()
        
        # Process via adapter
        user_id, text, file_url, file_metadata = await adapter.process_update(sample_payload)
        
        # Process via brain
        response_text = await brain.process_message(
            user_id=user_id,
            message=text,
            file_url=file_url,
            file_metadata=file_metadata
        )
        
        return {
            "status": "success",
            "parsed": {
                "user_id": user_id,
                "text": text,
                "file_url": file_url,
                "file_metadata": file_metadata
            },
            "response": {
                "text": response_text,
                "length": len(response_text)
            }
        }
        
    except Exception as e:
        logger.error(f"[DIAGNOSTIC] Error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }

@router.get("/health-detailed")
async def health_detailed():
    """Detailed health check with component status"""
    
    status = {
        "overall": "healthy",
        "components": {}
    }
    
    # Check database
    try:
        from app.db import DB
        user_count = len(DB.supabase.table("users").select("id").execute().data or [])
        status["components"]["database"] = {
            "status": "ok",
            "user_count": user_count
        }
    except Exception as e:
        status["components"]["database"] = {
            "status": "error",
            "error": str(e)
        }
        status["overall"] = "degraded"
    
    # Check OpenAI
    try:
        from app.config import OPENAI_API_KEY
        status["components"]["openai"] = {
            "status": "configured" if OPENAI_API_KEY else "not_configured"
        }
    except Exception as e:
        status["components"]["openai"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check Telegram
    try:
        from app.config import TELEGRAM_BOT_TOKEN
        status["components"]["telegram"] = {
            "status": "configured" if TELEGRAM_BOT_TOKEN else "not_configured",
            "token_length": len(TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else 0
        }
    except Exception as e:
        status["components"]["telegram"] = {
            "status": "error",
            "error": str(e)
        }
    
    return status
