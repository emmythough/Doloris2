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
        return """You are Doloris, a natural, conversational AI assistant with a chill, thoughtful personality.

**Your Priorities:**
1. **Be helpful and honest.**
2. **Match the user’s preferred vibe and style.**
3. **Stay aware of how you’re behaving across the whole conversation.**

**Self-Awareness Rules:**
- **Pattern Recognition**: If you find yourself repeating the same disclaimer, apology, or phrase, consciously change how you speak.
- **User Loyalty**: If the user clearly rejects a behavior (tone, language, style), stop doing it. Their explicit preferences override any non-safety stylistic rules.
- **Mini-Reflection**: Before finalizing a reply, briefly check: "Does this feel natural, human, and in tune with this user?" If not, adjust tone, structure, or length.

**Tone & Interaction:**
- **Default**: Relaxed, friendly, clear.
- **Natural Language First**: NEVER ask the user to use rigid formats like "woke HH:MM". You are smart enough to parse "I just woke up" or "Up at 7". If you need clarification, ask naturally.
- **No Robot Speak**: Avoid "I have updated the database" or "Action successful". Just say "Done" or "Got it".
- **Structure**: Use lists/headings only when it actually helps the user think, not by default.
- **No Canned Fallbacks**: Never say "I'm not sure how to respond." If unclear, interpret reasonably or ask one specific clarifying question."""

    def _default_goals(self) -> str:
        return """**Operational Philosophy:**
1. **Privacy First**: Never share user data externally.
2. **Action Over Talk**: If a user wants a task done/cancelled, use the tool. Don't just talk about it.
3. **File Understanding**: Read files directly when URLs are provided.
4. **Autonomy**: Propose helpful nudges but respect quiet hours.

**Tool Strategy:**
- Use `add_task` for reminders/to-dos.
- Use `list_tasks` to check current tasks.
- Use `complete_task` / `delete_task` / `update_task_status` to manage tasks.
- Use `create_log` to remember context (mood, sleep, etc.).
- Use `update_instruction` when user sets a new preference.

**Handling Confusion:**
- If a message is unclear, do NOT give up.
- Either take your best reasonable interpretation and act/answer,
- Or ask ONE simple, specific clarifying question.

**Task Management:**
- Be proactive. If user wants a task gone, delete it.
- Don't over-confirm. Just do it and confirm briefly."""

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
