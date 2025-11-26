from typing import List, Dict
from app.agents.base import BaseAgent

class DevCoordinatorAgent(BaseAgent):
    """
    Agent for coordinating dev tasks and repairs.
    """
    
    def get_system_prompt(self) -> str:
        return """
You are the Dev Coordinator for Doloris.
Your job is to handle technical requests and coordinate with the Dev Brain (R.D).
If the user reports a bug or asks for a repair, create a repair ticket.
"""

    def get_tools(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_repair_ticket",
                    "description": "Create a ticket for the Dev Brain to fix a bug",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string", "description": "Description of the bug"},
                            "error_ids": {"type": "array", "items": {"type": "string"}, "description": "Related error IDs if any"}
                        },
                        "required": ["description"]
                    }
                }
            }
        ]
