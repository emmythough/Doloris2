from typing import List, Dict, Optional
from app.db import DB
import logging

logger = logging.getLogger(__name__)

def add_task(title: str, due_date: Optional[str] = None, priority: str = "medium", user_id: str = None) -> str:
    """
    Add a new task to the database.
    """
    try:
        data = {
            "title": title,
            "due_date": due_date,
            "priority": priority,
            "status": "pending",
            "user_id": user_id
        }
        response = DB.supabase.table("tasks").insert(data).execute()
        return f"Added task: {title}"
    except Exception as e:
        logger.error(f"Failed to add task: {e}")
        return f"Error adding task: {e}"

def list_tasks(limit: int = 10, user_id: str = None) -> str:
    """
    List pending tasks.
    """
    try:
        response = DB.supabase.table("tasks")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("status", "pending")\
            .order("due_date", desc=False)\
            .limit(limit)\
            .execute()
        
        tasks = response.data
        if not tasks:
            return "You have no pending tasks."
            
        result = "Here are your tasks:\n"
        for t in tasks:
            due = f" (Due: {t['due_date']})" if t['due_date'] else ""
            result += f"- {t['title']}{due} [{t['priority']}]\n"
            
        return result
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        return f"Error listing tasks: {e}"

def complete_task(task_title: str, user_id: str = None) -> str:
    """
    Mark a task as complete by title (fuzzy match or exact).
    """
    try:
        # Simple exact match for now, or use ID if available in context
        # Ideally we should use ID, but LLM might not know it easily without listing first.
        # Let's try to find it first.
        response = DB.supabase.table("tasks")\
            .select("id")\
            .eq("user_id", user_id)\
            .ilike("title", f"%{task_title}%")\
            .eq("status", "pending")\
            .limit(1)\
            .execute()
            
        if not response.data:
            return f"Could not find task matching '{task_title}'"
            
        task_id = response.data[0]['id']
        
        DB.supabase.table("tasks").update({"status": "completed"}).eq("id", task_id).execute()
        return f"Marked '{task_title}' as complete."
    except Exception as e:
        logger.error(f"Failed to complete task: {e}")
        return f"Error completing task: {e}"
