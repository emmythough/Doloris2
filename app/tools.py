from app.db import DB
import json

# Tool Definitions Schema for OpenAI Responses API
# Note: Responses API uses flattened structure (name at top level, not nested in function)
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": "Add a new task to the user's list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The task description."},
                    "due_at": {"type": "string", "description": "ISO 8601 date string for deadline (optional)."},
                    "priority": {"type": "integer", "description": "Priority 1-5 (default 1)."}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List all pending tasks for the user.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Mark a task as complete. Use this when the user says they finished something or asks to mark a task done.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "The UUID of the task to complete."}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Permanently delete a task. Use when user wants to remove or cancel a task entirely.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "The UUID of the task to delete."}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_task_status",
            "description": "Update a task's status. Use to mark tasks as todo, in_progress, completed, or cancelled.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "The UUID of the task to update."},
                    "status": {"type": "string", "description": "New status: 'todo', 'in_progress', 'completed', or 'cancelled'."}
                },
                "required": ["task_id", "status"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_instruction",
            "description": "Update or add a behavioral instruction for the assistant.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scope": {"type": "string", "description": "Scope of instruction (e.g., 'global', 'health')."},
                    "content": {"type": "string", "description": "The instruction content."},
                    "is_active": {"type": "boolean", "description": "Whether the instruction is active."}
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_log",
            "description": "Log a life event or note (e.g., sleep, mood, workout).",
            "parameters": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Type of event (e.g., 'sleep', 'mood', 'work')."},
                    "summary": {"type": "string", "description": "Brief summary of the event."},
                    "details": {"type": "object", "description": "JSON details (optional)."},
                    "occurred_at": {"type": "string", "description": "ISO 8601 timestamp (optional)."}
                },
                "required": ["type", "summary"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "propose_nudge",
            "description": "Propose a proactive message to send to the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "The message content to send."},
                    "reason": {"type": "string", "description": "Internal reason for sending this nudge."}
                },
                "required": ["message", "reason"]
            }
        }
    }
]

# Tool Groupings by Intent
# Tool Groupings by Intent
TASK_TOOLS = [t for t in TOOLS_SCHEMA if t["function"]["name"] in ["add_task", "list_tasks", "complete_task", "delete_task", "update_task_status"]]
NOTE_TOOLS = [t for t in TOOLS_SCHEMA if t["function"]["name"] in ["create_log", "update_instruction"]]
FILE_TOOLS = [t for t in TOOLS_SCHEMA if t["function"]["name"] in ["create_log"]]  # File tools will be added in Phase 4
ALL_TOOLS = TOOLS_SCHEMA


# Tool Implementation Map
def execute_tool(tool_name: str, args: dict, user_id: str):
    if tool_name == "add_task":
        task = DB.add_task(user_id, **args)
        return f"Task added: {task.title} (ID: {task.id})"
    
    elif tool_name == "list_tasks":
        tasks = DB.get_pending_tasks(user_id)
        if not tasks:
            return "No pending tasks."
        return "\n".join([f"- {t.title} (ID: {t.id}, Status: {t.status.value})" for t in tasks])
    
    elif tool_name == "complete_task":
        task_id = args.get("task_id")
        result = DB.supabase.table("tasks").update({"status": "completed"}).eq("id", task_id).eq("user_id", user_id).execute()
        if result.data:
            return f"Task completed: {result.data[0].get('title', task_id)}"
        return f"Task not found: {task_id}"
    
    elif tool_name == "delete_task":
        task_id = args.get("task_id")
        result = DB.supabase.table("tasks").delete().eq("id", task_id).eq("user_id", user_id).execute()
        if result.data:
            return f"Task deleted: {result.data[0].get('title', task_id)}"
        return f"Task not found: {task_id}"
    
    elif tool_name == "update_task_status":
        task_id = args.get("task_id")
        status = args.get("status")
        result = DB.supabase.table("tasks").update({"status": status}).eq("id", task_id).eq("user_id", user_id).execute()
        if result.data:
            return f"Task status updated to '{status}': {result.data[0].get('title', task_id)}"
        return f"Task not found: {task_id}"
        
    elif tool_name == "update_instruction":
        instruction = DB.update_instruction(user_id, **args)
        return f"Instruction updated: {instruction.content} (Scope: {instruction.scope})"
        
    elif tool_name == "create_log":
        log = DB.create_log(user_id, **args)
        return f"Log created: {log.type} - {log.summary}"
        
    elif tool_name == "search_logs":
        # Simple search using ILIKE via Supabase
        query = args.get("query", "")
        response = DB.supabase.table("logs").select("*").ilike("summary", f"%{query}%").limit(5).execute()
        logs = response.data
        if not logs:
            return "No logs found matching query."
        return "\n".join([f"- [{l['created_at'][:10]}] {l['type']}: {l['summary']}" for l in logs])

    elif tool_name == "get_trace":
        try:
            from app.core.system_logger import system_logger
            trace_id = args.get("trace_id")
            events = system_logger.get_trace(trace_id)
            if not events:
                return f"No events found for trace {trace_id}"
            return json.dumps(events, indent=2, default=str)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"get_trace failed: {e}", exc_info=True)
            return f"❌ **Trace System Error**\n\nCouldn't retrieve trace: {str(e)}\n\nThis error has been logged for R.D to investigate."

    elif tool_name == "get_recent_errors":
        try:
            # Query system_events for errors
            response = DB.supabase.table("system_events")\
                .select("*")\
                .eq("status", "error")\
                .order("created_at", desc=True)\
                .limit(5)\
                .execute()
            errors = response.data
            if not errors:
                return "✅ No recent errors found. System is healthy!"
            return "⚠️ **Recent Errors:**\n" + "\n".join([f"- [{e['created_at'][:16]}] {e.get('event_type', 'unknown')}: {e.get('trace_id', 'N/A')}" for e in errors])
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"get_recent_errors failed: {e}", exc_info=True)
            return f"❌ **Error System Connection Failed**\n\n{str(e)}\n\nBut I'm still responding, so core systems work! Use /repair to investigate."
        
    return f"Tool {tool_name} not found."
