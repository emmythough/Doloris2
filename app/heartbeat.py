from fastapi import APIRouter, HTTPException
from app.db import DB
from app.openai_client import get_completion
from app.tools import TOOLS_SCHEMA, execute_tool
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
    
    # In a real app, we would iterate over all users with autonomous=True
    # For MVP, we'll just check our test user or a specific user if we had one.
    # Let's assume we iterate over all users who have interacted recently or have settings enabled.
    # Since we don't have a "get_all_users" easily exposed yet, let's just use the test user ID for demo
    # or fetch users from DB. Let's add get_all_users to DB first or just fetch one.
    
    # For MVP simplicity: We will skip the iteration and just return OK, 
    # OR we can implement a simple check for the user we created in tests.
    # Let's try to fetch the user with telegram_id=123456789 (Test User)
    user = DB.get_user_by_telegram_id(123456789)
    if not user:
        return {"status": "no_users_found"}
        
    # Build Snapshot
    tasks = DB.get_pending_tasks(user.id)
    tasks_due = "\n".join([f"- {t.title} (Due: {t.due_at})" for t in tasks if t.due_at]) or "None"
    
    logs = DB.get_recent_logs(user.id, limit=3)
    recent_logs = "\n".join([f"- {l.type}: {l.summary}" for l in logs]) or "None"
    
    instructions = DB.get_active_instructions(user.id)
    instruction_text = "\n".join([f"- {i.content}" for i in instructions]) or "None"
    
    prompt = HEARTBEAT_PROMPT.format(
        current_time=datetime.now().isoformat(),
        tasks_due=tasks_due,
        recent_logs=recent_logs,
        instructions=instruction_text
    )
    
    # Call OpenAI
    messages = [{"role": "system", "content": prompt}]
    
    # We need to add propose_nudge to tools if not already there (it's not in TOOLS_SCHEMA yet)
    # We will define it locally or update tools.py. Let's update tools.py first.
    # But for now, let's assume it's available.
    
    try:
        response = get_completion(messages, tools=TOOLS_SCHEMA)
        
        if response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call.function.name == "propose_nudge":
                    args = json.loads(tool_call.function.arguments)
                    # Execute nudge (log it and send telegram)
                    # We need a way to send telegram from here.
                    # We can import send_message from telegram_webhook but it might cause circular import.
                    # Better to move send_message to a utility or just import inside function.
                    from app.telegram_webhook import send_message
                    
                    message = args.get("message")
                    reason = args.get("reason")
                    
                    # Log nudge
                    # DB.create_nudge(user.id, message, reason) # Need to implement this
                    
                    # Send
                    await send_message(user.telegram_id, f"🔔 Nudge: {message}")
                    logger.info(f"Sent nudge to {user.id}: {message}")
                    return {"status": "nudged", "message": message}
                    
        return {"status": "silent"}
        
    except Exception as e:
        logger.error(f"Heartbeat error: {e}")
        return {"status": "error", "detail": str(e)}
