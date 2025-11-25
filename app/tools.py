from app.db import DB
import json

# Tool Definitions Schema for OpenAI Responses API
# Note: Responses API uses flattened structure (name at top level, not nested in function)
TOOLS_SCHEMA = [
    {
        "type": "function",
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
    },
    {
        "type": "function",
        "name": "list_tasks",
        "description": "List all pending tasks for the user.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "type": "function",
        "name": "complete_task",
        "description": "Mark a task as complete. Use this when the user says they finished something or asks to mark a task done.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "The UUID of the task to complete."}
            },
            "required": ["task_id"]
        }
    },
    {
        "type": "function",
        "name": "delete_task",
        "description": "Permanently delete a task. Use when user wants to remove or cancel a task entirely.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "The UUID of the task to delete."}
            },
            "required": ["task_id"]
        }
    },
    {
        "type": "function",
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
    },
    {
        "type": "function",
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
    },
    {
        "type": "function",
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
    },
    {
        "type": "function",
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
]

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
        
    return f"Tool {tool_name} not found."
