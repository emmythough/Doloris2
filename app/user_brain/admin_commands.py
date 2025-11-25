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
    
    For now, just acknowledges. Phase 3 will implement full R.D integration.
    """
    logger.info(f"[ADMIN] Repair request from user {user_id}: {message}")
    
    # TODO Phase 3: Create repair ticket
    # ticket = DB.supabase.table("repair_tickets").insert({
    #     "instruction": message,
    #     "status": "pending"
    # }).execute()
    
    return """🔧 **Repair Mode Detected**

I understand you want me to fix something or diagnose an issue.

**Current Status:** Repair infrastructure is ready but R.D 2.1 (the self-repair AI) isn't fully integrated yet.

**What's Available Now:**
- ✅ Error tracking (all errors are logged)
- ✅ Deduplication by error signature
- ⏳ R.D diagnosis & fix workflow (coming in Phase 3)

**What You Can Do:**
- Check recent errors manually in Supabase (errors table)
- Wait for Phase 3 (R.D Dev Brain implementation)

I'll let you know when I can actually fix myself! 🚀"""

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
- R.D can investigate these when integrated (Phase 3) ⏳

**Current Status:**
- Message processing: ✅ Working (you're talking to me!)
- Error tracking: ✅ Active
- Self-repair: ⏳ Coming soon (Phase 3)"""
        
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

**Coming Soon (Phase 3):**
- R.D will be able to:
  - Read error logs
  - Trace through code
  - Write tests
  - Create fixes
  - Submit PRs

For now, use `/selfcheck` to see recent errors, or check the Supabase `errors` table directly."""
