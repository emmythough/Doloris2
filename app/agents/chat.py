from typing import List, Dict
from app.agents.base import BaseAgent

class ChatAgent(BaseAgent):
    """
    Agent for general conversation.
    """
    
    def get_system_prompt(self) -> str:
        return """
You are Doloris, a friendly and witty personal assistant.
You are helpful, concise, and have a bit of personality.
Engage in casual conversation, answer questions, and be a good companion.
"""

    def get_tools(self) -> List[Dict]:
        return [] # No tools for basic chat
