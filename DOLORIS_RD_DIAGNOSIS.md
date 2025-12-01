# Doloris-R.D Integration Diagnosis
## Real-World Failure Analysis

**Date:** November 28, 2025  
**Source:** User conversation with Doloris showing multiple failures

---

## Problems Identified

### 1. ❌ Connection Errors to Trace System

**What Happened:**
```
User: "You had an error trying to connect to your brain. Can you check what that was?"
Doloris: "It seems there was an issue connecting to the trace system to retrieve specific trace information."
```

**Root Cause:** 
- Doloris tried to use `get_trace` tool
- Connection to Supabase `system_events` table failed
- Error was NOT properly logged or explained to user

**Code Location:** `app/tools.py` line 187-193
```python
elif tool_name == "get_trace":
    from app.core.system_logger import system_logger
    trace_id = args.get("trace_id")
    events = system_logger.get_trace(trace_id)  # <-- This failed
    if not events:
        return f"No events found for trace {trace_id}"
    return json.dumps(events, indent=2, default=str)
```

**The Problem:**
- When `system_logger.get_trace()` throws an exception, it's not caught
- Exception bubbles up and Doloris gives vague error message
- No details logged about WHY it failed

**Fix Needed:**
```python
elif tool_name == "get_trace":
    try:
        from app.core.system_logger import system_logger
        trace_id = args.get("trace_id")
        events = system_logger.get_trace(trace_id)
        if not events:
            return f"No events found for trace {trace_id}"
        return json.dumps(events, indent=2, default=str)
    except Exception as e:
        logger.error(f"get_trace failed: {e}", exc_info=True)
        return f"❌ Trace system error: {str(e)}. This has been logged for R.D to investigate."
```

---

### 2. ❌ Doloris Doesn't Understand R.D Brain

**What Happened:**
```
User: "How does the RD brain work?"
Doloris: "The RD brain, or 'Request-Driven' brain, processes requests and tasks..."
```

**This is WRONG!** R.D stands for "Repair Doloris", not "Request-Driven"

**Root Cause:**
- Doloris's knowledge cutoff is October 2023
- R.D brain was added in November 2025
- Doloris doesn't have R.D in its system prompt/self-model

**Code Location:** `app/core/self_model.py`

**Fix Needed:**
Add to Doloris's default personality/goals:

```python
**R.D Brain (Repair Doloris):**
- R.D is a separate AI agent that can fix bugs in my code
- R.D is NOT me - it's like a robot engineer that repairs me
- When user asks about R.D, explain: "R.D is my repair brain - an AI that can diagnose bugs, write tests, and create fixes"
- I can trigger R.D using admin commands: /repair, /selfcheck
- R.D works in background and creates GitHub PRs for fixes
```

---

### 3. ❌ /repair Command Didn't Create Ticket

**What Happened:**
```
User: "/repair"
Doloris: "Please provide a description of the bug or issue you're facing..."
User: "Two messages in a row is the bug"
Doloris: "Let's check the recent error logs..."
```

**The Problem:**
- User gave bug description but Doloris didn't create a repair ticket
- Doloris queried errors instead of passing description to R.D

**Root Cause:** `admin_commands.py` line 45-103

Current flow:
1. User says `/repair` with description
2. Code looks for error in `errors` table
3. If no error found → fails
4. **Doesn't use the user's bug description!**

**Fix Needed:**
```python
async def handle_repair_request(message: str, user_id: int) -> str:
    logger.info(f"[ADMIN] Repair request from user {user_id}: {message}")
    
    # Extract bug description from message
    bug_description = message.replace("/repair", "").strip()
    
    if not bug_description:
        return "Please describe the bug you want me to fix."
    
    # Create ticket with user's description (even without error_signature)
    ticket = DB.supabase.table("repair_tickets").insert({
        "instruction": bug_description,
        "error_signature": None,  # <-- OK to be None
        "status": "pending",
        "reported_by": str(user_id)
    }).execute()
    
    ticket_id = ticket.data[0]["id"]
    
    return f"""🤖 R.D (Repair Doloris):

Ticket #{ticket_id} created for: "{bug_description}"

I'll investigate and create a fix. You'll get updates as I work.

(This is R.D, not Doloris - I'm the robot that repairs her!)"""
```

---

### 4. ❌ /selfcheck Failed with Connection Error

**What Happened:**
```
User: "/selfcheck"
Doloris: "I am currently unable to perform a self-check due to a connection issue..."
```

**Root Cause:** `admin_commands.py` line 106-155

The code queries `errors` table:
```python
errors_result = DB.supabase.table("errors").select(...).execute()
```

**But this table might not exist or query failed!**

**Fix Needed:**
```python
async def handle_selfcheck(user_id: int) -> str:
    try:
        # Try errors table first
        try:
            errors_result = DB.supabase.table("errors")\
                .select("...")\
                .execute()
        except:
            # Fallback to system_events
            errors_result = DB.supabase.table("system_events")\
                .select("*")\
                .eq("status", "error")\
                .limit(5)\
                .execute()
        
        # ... rest of logic
        
    except Exception as e:
        logger.error(f"Selfcheck failed: {e}", exc_info=True)
        # STILL PROVIDE USEFUL INFO
        return f"""⚠️ Selfcheck had issues: {str(e)}

But I can tell you:
- ✅ I'm responding to you (obviously working!)
- ✅ Message processing works
- ❌ Database connection may have issues

Use /repair to have R.D investigate."""
```

---

### 5. ❌ R.D Not Identifying Itself

**What Happened:**
```
User: "Am I talking to RD?"
Doloris: "Nope, you're chatting with Doloris!"
```

This is correct, BUT when R.D DOES respond, user can't tell.

**Fix Needed:**
Every R.D message should start with:
```
🤖 R.D (Repair Doloris):
```

---

## Summary of Fixes Needed

| Issue | Priority | File | Fix |
|-------|----------|------|-----|
| Connection errors not handled | HIGH | app/tools.py | Add try-catch to get_trace |
| Doloris doesn't know about R.D | HIGH | app/core/self_model.py | Add R.D explanation to personality |
| /repair doesn't use bug description | HIGH | app/user_brain/admin_commands.py | Accept description even without error_signature |
| /selfcheck assumes errors table exists | MEDIUM | app/user_brain/admin_commands.py | Add fallback to system_events |
| R.D doesn't identify itself | HIGH | app/dev_brain/repair_agent.py | Prefix all messages with "🤖 R.D:" |
| No progress updates from R.D | MEDIUM | app/dev_brain/repair_agent.py | Send Telegram updates at each step |

---

## Test Case

**User Bug Report:**
> "Sending two messages in a row causes crashes"

**Expected Flow:**
1. User: `/repair Two messages in a row causes crashes`
2. Doloris → admin_commands.handle_repair_request()
3. Creates ticket in repair_tickets table
4. R.D worker picks up ticket
5. R.D sends: "🤖 R.D: Investigating 'two messages in a row'..."
6. R.D searches logs for related errors
7. R.D creates test + fix
8. R.D sends: "🤖 R.D: PR #43 created. Review at github.com/..."

**Actual Flow (BROKEN):**
1. User: `/repair`
2. Doloris: "Describe the bug"
3. User: "Two messages in a row causes crashes"
4. Doloris: "Let me check errors..."  ← WRONG!
5. Doloris tries `get_trace` → fails
6. Doloris: "Connection error"
7. → No ticket created, R.D never runs

---

## Action Items

1. Fix error handling in get_trace tool
2. Update Doloris's self-model to know about R.D
3. Fix /repair to accept bug descriptions
4. Add R.D identity to all R.D messages
5. Test with real `/repair` command

---

**This is a perfect real-world test case for improving the Doloris-R.D integration!**
