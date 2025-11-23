from fastapi import APIRouter, Request, HTTPException
from app.config import TELEGRAM_BOT_TOKEN
from app.agent import handle_user_message
import httpx
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

@router.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        logger.info(f"Received webhook data: {data}")
        
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")
            user_id = data["message"]["from"]["id"] # Telegram User ID
            
            if text:
                # Call the agent
                response_text = await handle_user_message(user_id, text)
                
                # Send response back to Telegram
                await send_message(chat_id, response_text)
                
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        # Don't raise 500 to Telegram to avoid retries on logic errors, just log it
        return {"status": "error", "message": str(e)}

async def send_message(chat_id: int, text: str):
    async with httpx.AsyncClient() as client:
        payload = {
            "chat_id": chat_id,
            "text": text
        }
        await client.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)
