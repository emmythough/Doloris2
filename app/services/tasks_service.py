"""
Tasks Service - Manages user tasks and to-dos

Extracted from DB class for modularity.
"""

import logging
from typing import List, Dict, Optional
from app.db import DB
from app.models import Task

logger = logging.getLogger(__name__)

class TasksService:
    """Service for managing tasks"""
    
    def __init__(self):
        self.db = DB
    
    def add_task(self, user_id: int, title: str, due_at: Optional[str] = None, priority: int = 1) -> Dict:
        """Add a new task"""
        try:
            task = self.db.add_task(user_id, title, due_at, priority)
            return {"success": True, "task_id": task.id, "task": task.dict()}
        except Exception as e:
            logger.error(f"Error adding task: {e}")
            return {"success": False, "error": str(e)}
    
    def list_tasks(self, user_id: int, status: str = "pending") -> Dict:
        """List tasks for a user"""
        try:
            tasks = self.db.get_pending_tasks(user_id)
            return {
                "success": True, 
                "tasks": [t.dict() for t in tasks]
            }
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            return {"success": False, "error": str(e)}
    
    def update_task(self, task_id: str, updates: Dict) -> Dict:
        """Update a task"""
        try:
            res = self.db.supabase.table("tasks").update(updates).eq("id", task_id).execute()
            if res.data:
                return {"success": True, "task": res.data[0]}
            return {"success": False, "error": "Task not found"}
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return {"success": False, "error": str(e)}
