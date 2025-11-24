"""
Message Endpoint - Handles incoming text messages

Normalizes input and passes to Brain.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.brain import get_brain

router = APIRouter()

class MessageRequest(BaseModel):
    user_id: int
    text: str

@router.post("/message")
async def handle_message(request: MessageRequest):
    """Process a text message"""
    try:
        brain = get_brain()
        response = await brain.process_message(
            user_id=request.user_id,
            message=request.text
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
