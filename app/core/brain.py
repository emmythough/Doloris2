"""
Doloris Brain - Main conversation orchestrator

Coordinates all components: self-model, model router, tools, and OpenAI.
"""

import logging
from typing import Dict, Any, Optional, List
from app.core.self_model import get_self_model
from app.core.model_router import ModelRouter, ModelTier
from app.core.tools_orchestrator import ToolsOrchestrator
from app.db import DB
from app.openai_client import OpenAIClient
from app.tools import TOOLS_SCHEMA
from datetime import datetime

logger = logging.getLogger(__name__)

class Brain:
    """The central intelligence engine"""
    
    def __init__(self):
        self.self_model = get_self_model()
        self.model_router = ModelRouter()
        self.tools_orchestrator = ToolsOrchestrator()
        self.openai_client = OpenAIClient()
    
    async def process_message(
        self,
        user_id: int,
        message: str,
        file_url: Optional[str] = None,
        file_metadata: Optional[Dict] = None
    ) -> str:
        """
        Process a user message and return a response
        
        Args:
            user_id: Telegram user ID
            message: User's message text
            file_url: Optional file URL if user sent a file
            file_metadata: Optional file metadata (name, type, size)
        
        Returns:
            Assistant's response text
        """
        logger.info(f"Processing message from user {user_id}: {message[:50]}...")
        
        try:
            # 1. Load user context
            user = DB.get_user_by_telegram_id(user_id)
            if not user:
                user = DB.create_user(user_id, name="User")
            
            # 2. Get user preferences
            preferences = self._get_user_preferences(user.id)
            
            # 3. Build conversation context
            context = self._build_context(user.id, message, file_url, file_metadata)
            
            # 4. Select model tier
            # Context is the full conversation text for analysis
            context_text = "\n".join([m["content"] for m in context["messages"] if isinstance(m["content"], str)])
            
            model_tier = self.model_router.select_model(
                message=message,
                context=context_text,
                has_tools=True,  # We always have tools available
                user_preference=preferences.get("thinking_mode"),
                file_attached=file_url is not None
            )
            model_name = self.model_router.get_model_name(model_tier)
            
            # 5. Call OpenAI
            response = await self._call_openai(
                model_name=model_name,
                messages=context["messages"],
                tools=TOOLS_SCHEMA if model_tier != ModelTier.TIER_3 else None,  # o1 doesn't support tools yet
                user_id=user.id
            )
            
            # 6. Save message
            DB.add_message(user.id, "user", message)
            DB.add_message(user.id, "assistant", response)
            
            return response
        
        except Exception as e:
            logger.error(f"Brain error: {e}", exc_info=True)
            return "I encountered an error processing your message. Please try again."
    
    def _get_user_preferences(self, user_id: int) -> Dict:
        """Get user preferences from database"""
        try:
            result = DB.supabase.table("preferences").select("*").eq("user_id", user_id).execute()
            if result.data and len(result.data) > 0:
                return result.data[0]
            return {}
        except:
            return {}
    
    def _build_context(
        self,
        user_id: int,
        message: str,
        file_url: Optional[str],
        file_metadata: Optional[Dict]
    ) -> Dict:
        """Build conversation context for OpenAI"""
        
        # System prompt with self-model
        system_prompt = self.self_model.get_system_prompt()
        
        # Add user instructions
        instructions = DB.get_active_instructions(user_id)
        if instructions:
            system_prompt += "\n\n**User Instructions:**\n"
            for inst in instructions:
                system_prompt += f"- {inst.content}\n"
        
        # Add recent logs for context
        logs = DB.get_recent_logs(user_id, limit=5)
        if logs:
            system_prompt += "\n\n**Recent Context:**\n"
            for log in logs:
                system_prompt += f"- {log.type}: {log.summary}\n"
        
        # Build messages array
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history
        history = DB.get_recent_messages(user_id, limit=10)
        for msg in history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add current message
        current_message = message
        if file_url:
            current_message += f"\n\n[File attached: {file_metadata.get('name', 'file')}]\nFile URL: {file_url}"
        
        messages.append({"role": "user", "content": current_message})
        
        return {"messages": messages}
    
    async def _call_openai(
        self,
        model_name: str,
        messages: List[Dict],
        tools: Optional[List[Dict]],
        user_id: int
    ) -> str:
        """Call OpenAI and handle tool calls"""
        
        # Initial call
        response = await self.openai_client.chat_completion(
            model=model_name,
            messages=messages,
            tools=tools
        )
        
        # Check for tool calls
        if response.get("tool_calls"):
            logger.info(f"Tool calls requested: {len(response['tool_calls'])}")
            
            # Execute tools
            tool_results = self.tools_orchestrator.execute_batch(
                response["tool_calls"],
                user_id
            )
            
            # Add tool results to messages
            messages.append({"role": "assistant", "content": response.get("content"), "tool_calls": response["tool_calls"]})
            for result in tool_results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": result["tool_call_id"],
                    "content": str(result["result"])
                })
            
            # Call OpenAI again with tool results
            final_response = await self.openai_client.chat_completion(
                model=model_name,
                messages=messages,
                tools=tools
            )
            return final_response.get("content", "Done!")
        
        return response.get("content", "I'm not sure how to respond to that.")

# Singleton instance
_brain = None

def get_brain() -> Brain:
    """Get the global brain instance"""
    global _brain
    if _brain is None:
        _brain = Brain()
    return _brain
