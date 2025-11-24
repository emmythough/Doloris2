"""
File Endpoint - Handles file metadata and URLs

Receives file info from adapters and passes to Brain.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.brain import get_brain

router = APIRouter()

class FileRequest(BaseModel):
    user_id: int
    file_url: str
    file_name: str
    file_type: str
    file_size: int
    caption: Optional[str] = None

@router.post("/file")
async def handle_file(request: FileRequest):
    """Process a file upload"""
    try:
        brain = get_brain()
        
        # Create a message context for the file
        message = request.caption or "I sent a file."
        
        response = await brain.process_message(
            user_id=request.user_id,
            message=message,
            file_url=request.file_url,
            file_metadata={
                "name": request.file_name,
                "type": request.file_type,
                "size": request.file_size
            }
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
