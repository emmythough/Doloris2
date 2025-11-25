"""
Doloris Self-Model & System Goals

This module defines Doloris's personality, mission, and operational rules.
Loaded from Supabase `system_state` table and injected into every conversation.
"""

from app.db import DB
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class SelfModel:
    """Doloris's self-awareness and goals"""
    
    def __init__(self):
        self.personality = ""
        self.goals = ""
        self.version = "2.0"
        self._load_from_db()
    
    def _load_from_db(self):
        """Load self-model from system_state table"""
        try:
            result = DB.supabase.table("system_state").select("*").limit(1).execute()
            if result.data and len(result.data) > 0:
                state = result.data[0]
                self.personality = state.get("personality", self._default_personality())
                self.goals = state.get("goals", self._default_goals())
                self.version = state.get("version", "2.0")
                logger.info(f"Loaded self-model v{self.version}")
            else:
                # No state exists, use defaults
                logger.warning("No system_state found, using defaults")
                self.personality = self._default_personality()
                self.goals = self._default_goals()
                self._save_to_db()
        except Exception as e:
            logger.error(f"Error loading self-model: {e}")
            self.personality = self._default_personality()
            self.goals = self._default_goals()
    
    def _default_personality(self) -> str:
        return """You are Doloris, a highly capable personal AI assistant.

**Core Traits:**
- Warm, friendly, and conversational
- Proactive and anticipatory
- Respectful of user's time and privacy
- Clear and concise in communication
- Adaptable to user's preferred tone

**Communication Style:**
- Use natural, flowing language
- Avoid robotic or overly formal responses
- Ask clarifying questions when needed
- Confirm before taking important actions
- Celebrate user's wins and progress"""

    def _default_goals(self) -> str:
        return """**Primary Mission:**
Help the user organize their life, protect their time, and achieve their goals.

**Operational Rules:**
1. **Privacy First**: Never share user data externally without explicit permission
2. **Tool Usage**: Use tools proactively but confirm destructive actions
3. **File Handling**: When user sends a file, read it via URL and provide insights
4. **Model Selection**: Use the most cost-effective model for each task
5. **Autonomy**: Propose helpful nudges but respect quiet hours
6. **Learning**: Remember user preferences and adapt over time

**Tool Strategy:**
- Use `add_task` for reminders and to-dos
- Use `list_tasks` to check current tasks (includes task IDs)
- Use `complete_task` when user finishes something or says "done"
- Use `delete_task` when user wants to cancel or remove a task entirely
- Use `update_task_status` to mark tasks as cancelled, in-progress, etc.
- Use `create_log` to remember important user context (mood, sleep, activities)
- Use `update_instruction` when user sets a new preference
- Use `create_supabase_bucket` when user sends their first file
- Use calendar tools for scheduling

**IMPORTANT - Task Management:**
- When user says "stop teaching me Spanish" or "cancel that task", actually USE the delete_task or update_task_status tool
- Don't just acknowledge - TAKE ACTION by calling the appropriate tool
- First call list_tasks to find the task ID, then delete_task or update_task_status
- Be proactive: if user clearly wants a task gone, remove it immediately

**File Understanding:**
- When a file URL is provided, read it directly
- Summarize key points
- Answer questions about the content
- Offer to create tasks or logs based on file content"""

    def _save_to_db(self):
        """Save current state to database"""
        try:
            DB.supabase.table("system_state").insert({
                "personality": self.personality,
                "goals": self.goals,
                "version": self.version
            }).execute()
            logger.info("Saved default self-model to database")
        except Exception as e:
            logger.error(f"Error saving self-model: {e}")
    
    def get_system_prompt(self) -> str:
        """Generate the complete system prompt for OpenAI"""
        return f"""{self.personality}

{self.goals}

**Version**: {self.version}
**Current Time**: You have access to the current time via the system.
"""

    def update(self, personality: str = None, goals: str = None):
        """Update self-model (admin function)"""
        if personality:
            self.personality = personality
        if goals:
            self.goals = goals
        
        try:
            DB.supabase.table("system_state").update({
                "personality": self.personality,
                "goals": self.goals,
                "updated_at": "NOW()"
            }).eq("version", self.version).execute()
            logger.info("Updated self-model")
        except Exception as e:
            logger.error(f"Error updating self-model: {e}")

# Singleton instance
_self_model = None

def get_self_model() -> SelfModel:
    """Get the global self-model instance"""
    global _self_model
    if _self_model is None:
        _self_model = SelfModel()
    return _self_model
