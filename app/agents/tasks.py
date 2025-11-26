from typing import List, Dict
from app.agents.base import BaseAgent
# from app.tools.database import add_task, list_tasks, complete_task # Assuming these exist or will be created

class TasksAgent(BaseAgent):
    """
    Agent for managing tasks and reminders.
    """
    
    def get_system_prompt(self) -> str:
        return """
You are Doloris, a highly efficient personal assistant.
Your primary role is to manage the user's tasks and reminders.
Always confirm actions clearly (e.g., "Added task: ...").
If the user asks to list tasks, format them nicely.
"""

    def get_tools(self) -> List[Dict]:
        # Return tool definitions compatible with OpenAI
        # For now, returning empty list until tools are defined
        return [
            {
                "type": "function",
                "function": {
                    "name": "add_task",
                    "description": "Add a new task to the list",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Task title"},
                            "due_date": {"type": "string", "description": "Due date (ISO format preferred)"},
                            "priority": {"type": "string", "enum": ["low", "medium", "high"]}
                        },
                        "required": ["title"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_tasks",
                    "description": "List pending tasks",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "default": 10}
                        }
                    }
                }
            }
        ]
