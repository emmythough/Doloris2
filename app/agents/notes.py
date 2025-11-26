from typing import List, Dict
from app.agents.base import BaseAgent
from app.tools import NOTE_TOOLS, TOOLS_SCHEMA

class NotesAgent(BaseAgent):
    """
    Agent for handling notes, logs, and knowledge retrieval.
    """
    
    def get_system_prompt(self) -> str:
        return """
You are the Notes & Knowledge Agent for Doloris.
Your role is to help the user log life events, thoughts, and retrieve information from their past logs.
When the user wants to log something, use the 'create_log' tool.
When the user asks about past events or logs, use the 'search_logs' tool.
Be concise and helpful.
"""

    def get_tools(self) -> List[Dict]:
        # We need create_log and search_logs
        # NOTE_TOOLS in tools.py has create_log. We need to find search_logs in TOOLS_SCHEMA manually or update grouping
        # For simplicity, let's filter TOOLS_SCHEMA
        return [t for t in TOOLS_SCHEMA if t["function"]["name"] in ["create_log", "search_logs"]]
