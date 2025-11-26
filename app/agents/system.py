from typing import List, Dict
from app.agents.base import BaseAgent
from app.tools import TOOLS_SCHEMA

class SystemAgent(BaseAgent):
    """
    Agent for system debugging and trace queries.
    """
    
    def get_system_prompt(self) -> str:
        return """
You are the System & Trace Agent for Doloris.
Your role is to help debug the system by looking up trace IDs and error logs.
Use 'get_trace' to inspect a specific request trace.
Use 'get_recent_errors' to see what went wrong recently.
Explain technical details in a way that helps the user understand what happened.
"""

    def get_tools(self) -> List[Dict]:
        return [t for t in TOOLS_SCHEMA if t["function"]["name"] in ["get_trace", "get_recent_errors"]]
