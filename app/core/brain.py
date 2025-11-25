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
        logger.info(f"[BRAIN] 🧠 Processing message from user {user_id}: '{message[:50]}...'")
        
        try:
            # 1. Load user context
            logger.info(f"[BRAIN] 📋 Loading user context...")
            user = DB.get_user_by_telegram_id(user_id)
            if not user:
                logger.info(f"[BRAIN] 🆕 Creating new user for telegram_id={user_id}")
                user = DB.create_user(user_id, name="User")
            
            logger.info(f"[BRAIN] ✅ User loaded: id={user.id}")
            
            # 2. Get user preferences
            logger.info(f"[BRAIN] ⚙️ Loading preferences...")
            preferences = self._get_user_preferences(user.id)
            
            # 3. Build conversation context
            logger.info(f"[BRAIN] 📝 Building context...")
            context = self._build_context(user.id, message, file_url, file_metadata)
            
            # 4. Select model tier
            context_text = "\n".join([m["content"] for m in context["messages"] if isinstance(m["content"], str)])
            
            logger.info(f"[BRAIN] 🔀 Selecting model...")
            model_tier = self.model_router.select_model(
                message=message,
                context=context_text,
                has_tools=True,
                user_preference=preferences.get("thinking_mode"),
                file_attached=file_url is not None
            )
            model_name = self.model_router.get_model_name(model_tier)
            logger.info(f"[BRAIN] ✅ Selected model: {model_name} (tier: {model_tier.value})")
            
            # 5. Call OpenAI
            logger.info(f"[BRAIN] 🌐 Calling OpenAI...")
            response = await self._call_openai(
                model_name=model_name,
                messages=context["messages"],
                tools=TOOLS_SCHEMA if model_tier != ModelTier.TIER_3 else None,
                user_id=user.id
            )
            
            logger.info(f"[BRAIN] ✅ Got response: '{response[:100]}...'")
            
            # 6. Save message
            logger.info(f"[BRAIN] 💾 Saving messages to DB...")
            DB.add_message(user.id, "user", message)
            DB.add_message(user.id, "assistant", response)
            
            logger.info(f"[BRAIN] ✅ Process complete!")
            return response
        
        except Exception as e:
            # Log error for R.D diagnosis
            import sys
            from app.middleware import log_error
            
            try:
                error_signature = log_error(type(e), e, sys.exc_info()[2], service='brain')
                logger.error(f"[BRAIN] 🔖 Error signature: {error_signature}")
            except Exception as log_err:
                logger.error(f"[BRAIN] ⚠️ Failed to log error: {log_err}")
            
            logger.error(f"[BRAIN] ❌ ERROR: {e}", exc_info=True)
            
            # Return a helpful error message instead of a generic one
            error_msg = str(e).lower()
            
            if "openai" in error_msg or "api" in error_msg:
                return "I'm having trouble connecting to my AI service right now. Please try again in a moment."
            elif "database" in error_msg or "supabase" in error_msg:
                return "I'm having trouble accessing my memory right now. Your message was received, but I couldn't process it fully."
            elif "timeout" in error_msg:
                return "That took too long to process. Could you try again with a simpler request?"
            else:
                return "I encountered an unexpected error. I'm still here though - feel free to try something else!"
    
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
        
        try:
            # Initial call (no temperature - GPT-5 only supports default)
            response = await self.openai_client.chat_completion(
                model=model_name,
                messages=messages,
                tools=tools
            )
            
            # Check for tool calls
            if response.get("tool_calls"):
                logger.info(f"[BRAIN] 🛠️ Tool calls requested: {len(response['tool_calls'])}")
                
                try:
                    # Execute tools
                    tool_results = self.tools_orchestrator.execute_batch(
                        response["tool_calls"],
                        user_id
                    )
                    
                    # Add tool results to messages
                    # IMPORTANT: content can be None when using tools, use empty string as fallback
                    initial_content = response.get("content") or ""
                    messages.append({"role": "assistant", "content": initial_content, "tool_calls": response["tool_calls"]})
                    for result in tool_results:
                        messages.append({
                            "role": "tool",
                            "tool_call_id": result["tool_call_id"],
                            "content": str(result["result"])
                        })
                    
                    # Call OpenAI again with tool results (no temperature)
                    final_response = await self.openai_client.chat_completion(
                        model=model_name,
                        messages=messages,
                        tools=tools
                    )
                    
                    # Get final content, ensure it's not empty
                    final_content = final_response.get("content", "").strip()
                    if not final_content:
                        logger.warning("[BRAIN] ⚠️ OpenAI returned empty content after tool execution")
                        return "I've completed that task for you!"
                    
                    return final_content
                    
                except Exception as tool_error:
                    logger.error(f"[BRAIN] ❌ Error executing tools: {tool_error}", exc_info=True)
                    return "I tried to perform that action, but ran into an issue. The task might not have completed."
            
            # No tool calls - return direct response
            content = response.get("content", "").strip()
            if not content:
                logger.warning("[BRAIN] ⚠️ OpenAI returned empty content (no tools)")
                return "I'm not sure how to respond to that. Could you rephrase?"
            
            return content
            
        except Exception as e:
            # Log error for R.D diagnosis  
            import sys
            from app.middleware import log_error
            
            try:
                error_signature = log_error(type(e), e, sys.exc_info()[2], service='openai_client')
                logger.error(f"[BRAIN] 🔖 Error signature: {error_signature}")
            except Exception as log_err:
                logger.error(f"[BRAIN] ⚠️ Failed to log error: {log_err}")
            
            logger.error(f"[BRAIN] ❌ Error calling OpenAI: {e}", exc_info=True)
            return "I'm having trouble thinking right now. Please try again in a moment."

# Singleton instance
_brain = None

def get_brain() -> Brain:
    """Get the global brain instance"""
    global _brain
    if _brain is None:
        _brain = Brain()
    return _brain
