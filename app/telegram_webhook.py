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
            
            logger.info(f"Processing message from user {user_id}: {text}")
            
            if text:
                try:
                    # Call the agent
                    logger.info(f"Calling agent for user {user_id}")
                    response_text = await handle_user_message(user_id, text)
                    logger.info(f"Agent response: {response_text}")
                    
                    # Send response back to Telegram
                    logger.info(f"Sending response to chat {chat_id}")
                    await send_message(chat_id, response_text)
                    logger.info(f"Response sent successfully")
                except Exception as agent_error:
                    logger.error(f"Agent error: {agent_error}", exc_info=True)
                    # Send error message to user
                    await send_message(chat_id, "Sorry, I encountered an error. Please try again.")
                
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        # Don't raise 500 to Telegram to avoid retries on logic errors, just log it
        return {"status": "error", "message": str(e)}

async def send_message(chat_id: int, text: str):
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "chat_id": chat_id,
                "text": text
            }
            response = await client.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)
            logger.info(f"Telegram API response: {response.status_code} - {response.text}")
            return response
    except Exception as e:
        logger.error(f"Error sending message: {e}", exc_info=True)
        raise
