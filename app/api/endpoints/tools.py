"""
Tools Endpoint - Internal endpoints for tool execution

Used by OpenAI to execute tools securely via the backend.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any
from app.core.tools_orchestrator import ToolsOrchestrator
from app.config import WEBHOOK_SECRET

router = APIRouter()

class ToolRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    user_id: int
    secret: str

@router.post("/execute")
async def execute_tool(request: ToolRequest):
    """Execute a tool (Internal only)"""
    # Simple security check
    if request.secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
        
    try:
        result = ToolsOrchestrator.execute_tool(
            tool_name=request.tool_name,
            arguments=request.arguments,
            user_id=request.user_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
