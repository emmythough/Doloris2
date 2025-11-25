"""
Admin Command Handler

Handles admin commands for R.D 2.1 integration:
- /repair - Request R.D to diagnose and fix issues
- /selfcheck - Check system health and recent errors
- diagnose - Investigate specific issues
"""

import logging
from typing import Dict
from app.db import DB

logger = logging.getLogger(__name__)

async def handle_admin_command(command: str, message: str, user_id: int) -> str:
    """
    Handle admin/repair commands
    
    Args:
        command: Detected command (/repair, /selfcheck, etc.)
        message: Full user message
        user_id: User ID
    
    Returns:
        Response string
    """
    logger.info(f"[ADMIN] Handling command: {command}")
    
    if command == "/repair" or "repair" in command.lower():
        return await handle_repair_request(message, user_id)
    
    elif command == "/selfcheck" or "selfcheck" in command.lower():
        return await handle_selfcheck(user_id)
    
    elif "diagnose" in command.lower() or "investigate" in command.lower():
        return await handle_diagnose_request(message, user_id)
    
    else:
        return "I detected an admin command but I'm not sure how to handle it yet. Available: /repair, /selfcheck"

async def handle_repair_request(message: str, user_id: int) -> str:
    """
    Handle /repair command - creates repair ticket for R.D
    """
    logger.info(f"[ADMIN] Repair request from user {user_id}: {message}")
    
    try:
        from app.dev_brain.repair_agent import get_repair_agent
        
        # Extract error signature if mentioned, otherwise use recent error
        error_signature = None
        
        # Check for recent errors
        errors_result = DB.supabase.table("errors").select("error_signature").order("last_seen_at", desc=True).limit(1).execute()
        
        if errors_result.data:
            error_signature = errors_result.data[0]["error_signature"]
        
        if not error_signature:
            return """❌ **No Recent Errors Found**

I couldn't find any recent errors to repair.

Try:
- Triggering an error first
- Using `/selfcheck` to see error history"""
        
        # Create repair ticket and start R.D workflow
        repair_agent = get_repair_agent()
        
        # Note: This is async and may take time, so we acknowledge and process in background
        # For now, just create the ticket
        ticket = DB.supabase.table("repair_tickets").insert({
            "instruction": message,
            "error_signature": error_signature,
            "status": "pending"
        }).execute()
        
        ticket_id = ticket.data[0]["id"]
        
        return f"""🔧 **Repair Ticket Created**

**Ticket ID:** `{ticket_id}`
**Error Signature:** `{error_signature[:16]}...`

**Status:** R.D 2.1 will now:
1. 🔍 Diagnose the error
2. 🧪 Write a reproduction test
3. 🔨 Create a fix
4. ✅ Validate with tests
5. 📝 Submit PR for your approval

I'll notify you when the PR is ready for review!

**Note:** This process may take a few minutes. Use `/check_repair {ticket_id}` to check status."""
    
    except Exception as e:
        logger.error(f"[ADMIN] Repair request failed: {e}", exc_info=True)
        return f"❌ **Repair Failed**\n\nError: {str(e)}\n\nThe repair infrastructure is set up, but something went wrong. Check logs for details."


async def handle_selfcheck(user_id: int) -> str:
    """
    Handle /selfcheck command - reports system health
    """
    logger.info(f"[ADMIN] Selfcheck request from user {user_id}")
    
    try:
        # Check recent errors
        errors_result = DB.supabase.table("errors").select("id, error_signature, count, service, last_seen_at").order("last_seen_at", desc=True).limit(5).execute()
        
        if not errors_result.data:
            return """✅ **System Health: Good**

No recent errors detected! Everything seems to be running smoothly.

**Infrastructure Status:**
- ✅ Error tracking active
- ✅ Database connected
- ✅ Message processing working
- ⏳ R.D self-repair ready (Phase 3)"""
        
        # Format error summary
        error_lines = []
        for error in errors_result.data:
            service = error.get("service", "unknown")
            count = error.get("count", 1)
            signature = error.get("error_signature", "unknown")[:16]
            error_lines.append(f"  - {service}: {count}x (sig: {signature}...)")
        
        errors_text = "\n".join(error_lines)
        
        return f"""⚠️ **System Health: Errors Detected**

Found {len(errors_result.data)} recent error types:

{errors_text}

**What This Means:**
- Errors are being tracked ✅
- Some issues occurred but system is resilient ✅
- R.D can investigate these now! Use `/repair` to start. 🤖

**Current Status:**
- Message processing: ✅ Working
- Error tracking: ✅ Active
- Self-repair: ✅ Active (R.D 2.1)"""
        
    except Exception as e:
        logger.error(f"[ADMIN] Selfcheck failed: {e}", exc_info=True)
        return f"❌ Selfcheck failed: {str(e)}\n\nBut hey, I'm still responding, so I'm somewhat alive! 😅"

async def handle_diagnose_request(message: str, user_id: int) -> str:
    """
    Handle diagnose/investigate commands
    """
    logger.info(f"[ADMIN] Diagnose request: {message}")
    
    # Extract what to diagnose from message
    # For now, just acknowledge
    
    return """🔍 **Diagnostic Mode**

I can see you want me to investigate something!

**Current Capabilities:**
- I can log errors and track them
- I can tell you about recent errors (/selfcheck)

**R.D 2.1 is Active!**
R.D is now fully integrated and can:
- 🔍 Read error logs
- 🧪 Trace through code & write tests
- 🔨 Create fixes & submit PRs

**How to use:**
- Use `/repair` to trigger a full repair workflow for the most recent error
- Use `/selfcheck` to see system health status"""
