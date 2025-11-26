import json
import logging
from typing import Dict, List, Any
from app.db import DB
from app.openai_client import openai_client

logger = logging.getLogger(__name__)

class ContextManager:
    """
    Manages context loading for agents.
    Implements Hybrid Memory:
    1. Relational (User, Tasks)
    2. Vector (Semantic Search - Placeholder)
    3. Conversation (Rolling Summaries)
    """
    
    @staticmethod
    def get_user_profile(user_id: str) -> Dict:
        try:
            response = DB.supabase.table("users").select("*").eq("id", user_id).single().execute()
            return response.data or {}
        except Exception:
            return {}

    @staticmethod
    def get_recent_tasks(user_id: str, limit: int = 5) -> List[Dict]:
        try:
            response = DB.supabase.table("tasks")\
                .select("title, due_date, priority, status")\
                .eq("user_id", user_id)\
                .eq("status", "pending")\
                .order("due_date", desc=False)\
                .limit(limit)\
                .execute()
            return response.data or []
        except Exception:
            return []

    @staticmethod
    def get_conversation_history(user_id: str, limit: int = 10) -> List[Dict]:
        # TODO: Implement actual history fetching from DB
        # For now, return empty or mock
        return []

    @staticmethod
    async def build_context(user_id: str, agent_type: str) -> Dict[str, Any]:
        """
        Builds the context dictionary for a specific agent.
        """
        context = {
            "user": ContextManager.get_user_profile(user_id)
        }
        
        if agent_type == "tasks":
            context["tasks"] = ContextManager.get_recent_tasks(user_id)
            
        # TODO: Add Vector Search results for 'notes' agent
        
        return context

    @staticmethod
    async def compress_history(user_id: str, messages: List[Dict]) -> str:
        """
        Compresses old conversation history into a summary.
        """
        if not messages:
            return ""
            
        try:
            # Call LLM to summarize
            response = await openai_client.chat_completion(
                messages=[
                    {"role": "system", "content": "Summarize the following conversation concisely."},
                    {"role": "user", "content": json.dumps(messages)}
                ],
                model="gpt-4o-mini"
            )
            return response.get("content", "")
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return ""
