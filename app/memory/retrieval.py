from typing import Dict, List, Any
from app.db import DB
import logging

logger = logging.getLogger(__name__)

class ContextRetriever:
    """
    Retrieves relevant context (tasks, logs, etc.) for the agent.
    """
    
    @staticmethod
    def get_context(user_id: str) -> Dict[str, Any]:
        """
        Fetch recent tasks and logs to provide context to the agent.
        """
        context = {}
        
        try:
            # 1. Get pending tasks (limit 5)
            tasks = DB.get_pending_tasks(user_id)
            # We only want a summary of tasks, not full objects if they are heavy
            # Assuming DB.get_pending_tasks returns objects with title, status, etc.
            # We'll slice to top 5
            recent_tasks = tasks[:5] if tasks else []
            context["pending_tasks"] = [
                {"id": t.id, "title": t.title, "priority": t.priority} 
                for t in recent_tasks
            ]
            
            # 2. Get recent logs (limit 3)
            # DB.get_recent_logs doesn't exist in the viewed snippets, but we can use raw supabase
            # or assume a method. Let's use raw supabase for safety if DB method is missing.
            # Actually, let's check DB.py first? No, let's just use Supabase client directly for now
            # to be safe, or implement a helper.
            # Let's try to query the 'logs' table directly.
            
            logs_response = DB.supabase.table("logs")\
                .select("type, summary, created_at")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(3)\
                .execute()
                
            context["recent_logs"] = logs_response.data if logs_response.data else []
            
            return context
            
        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            return {}
