from fastapi import APIRouter, HTTPException
from app.db import DB
from app.openai_client import openai_client
# from app.tools import TOOLS_SCHEMA, execute_tool # Legacy tools, need update if used
from app.channels.telegram import TelegramClient
from datetime import datetime, timedelta
import logging
import json

router = APIRouter()
logger = logging.getLogger(__name__)

HEARTBEAT_PROMPT = """You are the autonomous subconscious of Doloris.
Your goal is to check the user's status and decide if a proactive "nudge" is helpful.

Current Time: {current_time}

User Context:
- Tasks due soon: {tasks_due}
- Recent Logs: {recent_logs}
- Active Instructions: {instructions}

Rules:
1. ONLY propose a nudge if it's genuinely useful (e.g., reminder for upcoming task, sleep check).
2. Do NOT spam. If everything is fine, do nothing.
3. If you decide to nudge, use the `propose_nudge` tool.
4. If no nudge is needed, reply with "Status OK".
"""

@router.post("/trigger")
async def heartbeat_trigger():
    """
    Called by a cron job every X minutes.
    """
    logger.info("Heartbeat triggered")
    
    # Mock user for now
    user_id = "123456789" # Mock ID
    
    # Build Snapshot (Mocked DB calls for now as DB module might need update)
    # tasks = DB.get_pending_tasks(user.id)
    tasks_due = "None"
    recent_logs = "None"
    instruction_text = "None"
    
    prompt = HEARTBEAT_PROMPT.format(
        current_time=datetime.now().isoformat(),
        tasks_due=tasks_due,
        recent_logs=recent_logs,
        instructions=instruction_text
    )
    
    # Call OpenAI
    messages = [{"role": "system", "content": prompt}]
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "propose_nudge",
                "description": "Propose a proactive nudge to the user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "The message to send"},
                        "reason": {"type": "string", "description": "Why you are nudging"}
                    },
                    "required": ["message", "reason"]
                }
            }
        }
    ]
    
    try:
        response = await openai_client.chat_completion(messages, tools=tools, model="gpt-4o-mini")
        content = response.get("content", "")
        tool_calls = response.get("tool_calls", [])
        
        if tool_calls:
            for tool_call in tool_calls:
                if tool_call["name"] == "propose_nudge":
                    args = json.loads(tool_call["arguments"])
                    message = args.get("message")
                    
                    # Send
                    await TelegramClient.send_message(user_id, f"🔔 Nudge: {message}")
                    logger.info(f"Sent nudge to {user_id}: {message}")
                    return {"status": "nudged", "message": message}
                    
        return {"status": "silent"}
        
    except Exception as e:
        logger.error(f"Heartbeat error: {e}")
        return {"status": "error", "detail": str(e)}
