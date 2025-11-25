"""
Doloris Brain - Main conversation orchestrator

Handles message processing with intent classification and model routing.
"""

import logging
from typing import Dict, List, Optional
from app.db import DB
from app.openai_client import OpenAIClient
from app.core.model_router import ModelRouter
from app.core.self_model import get_self_model
from app.core.tools_orchestrator import ToolsOrchestrator
from app.user_brain.intent_classifier import get_intent_classifier
from app.user_brain.admin_commands import handle_admin_command

logger = logging.getLogger(__name__)

class Brain:
    """Main conversation orchestrator for Doloris"""
    
    def __init__(self):
        self.openai_client = OpenAIClient()
        self.model_router = ModelRouter()
        self.self_model = get_self_model()
        self.tools_orchestrator = ToolsOrchestrator()
        self.intent_classifier = get_intent_classifier()
        logger.info("[BRAIN] 🧠 Brain initialized")
    
    async def process_message(
        self,
        user_id: int,
        message: str,
        file_url: Optional[str] = None,
        file_metadata: Optional[Dict] = None
    ) -> str:
        """
        Main entry point for processing user messages
        
        Args:
            user_id: Telegram User ID (integer)
            message: User message text
            file_url: Optional URL to file
            file_metadata: Optional file metadata
        """
        telegram_id = user_id
        logger.info(f"[BRAIN] 📥 Processing message from telegram_id {telegram_id}: '{message[:50]}...'")
        
        try:
            # Step 0: Resolve Telegram ID to User UUID
            user = DB.get_user_by_telegram_id(telegram_id)
            if not user:
                logger.info(f"[BRAIN] 👤 New user detected: {telegram_id}")
                user = DB.create_user(telegram_id=telegram_id)
            
            # Use internal UUID for all DB operations
            internal_user_id = user.id
            logger.info(f"[BRAIN] 🆔 Resolved to internal user_id: {internal_user_id}")
            
            # Step 1: Classify intent
            intent_result = await self.intent_classifier.classify(message)
            intent = intent_result.get("intent", "chat")
            command = intent_result.get("command")
            
            logger.info(f"[BRAIN] 🎯 Intent: {intent}, Command: {command}")
            
            # Step 2: Handle admin commands separately
            if intent == "admin":
                logger.info(f"[BRAIN] 🔧 Routing to admin handler")
                # Pass telegram_id to admin commands as they might need it for auth checks
                return await handle_admin_command(command or message, message, telegram_id)
            
            # Step 3: Build context using UUID
            context = await self._build_context(
                user_id=internal_user_id,
                message=message,
                file_url=file_url,
                file_metadata=file_metadata
            )
            
            # Step 4: Select model based on intent and context
            has_tools = intent in ["task", "note"]
            model_tier = self.model_router.select_model(
                message=message,
                context=str(context),
                has_tools=has_tools,
                file_attached=file_url is not None
            )
            model_name = self.model_router.get_model_name(model_tier)
            
            logger.info(f"[BRAIN] 🤖 Selected model: {model_name}")
            
            # Step 5: Get tools for this intent
            tools = self.tools_orchestrator.get_tools_for_intent(intent)
            
            # Step 6: Call OpenAI
            response = await self._call_openai(
                model_name=model_name,
                messages=context["messages"],
                tools=tools,
                user_id=internal_user_id
            )
            
            # Step 7: Save message to history
            DB.add_message(internal_user_id, "user", message)
            DB.add_message(internal_user_id, "assistant", response)
            
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
            
            # Return a helpful error message
            error_msg = str(e).lower()
            
            if "openai" in error_msg or "api" in error_msg:
                return "I'm having trouble connecting to my AI service right now. Please try again in a moment."
            elif "database" in error_msg or "supabase" in error_msg:
                return "I'm having trouble accessing my memory right now. Your message was received, but I couldn't process it fully."
            elif "timeout" in error_msg:
                return "That took too long to process. Could you try again with a simpler request?"
            else:
                return "I encountered an unexpected issue. Please try again or rephrase your message."
    
    async def _build_context(
        self,
        user_id: str,
        message: str,
        file_url: Optional[str] = None,
        file_metadata: Optional[Dict] = None
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
        user_id: str
    ) -> str:
        """Call OpenAI and handle tool calls"""
        
        try:
            # Initial call
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
                    messages.append({
                        "role": "assistant",
                        "content": response.get("content"),
                        "tool_calls": response["tool_calls"]
                    })
                    
                    for result in tool_results:
                        messages.append({
                            "role": "tool",
                            "tool_call_id": result["tool_call_id"],
                            "content": result["content"]
                        })
                    
                    # Get final response
                    final_response = await self.openai_client.chat_completion(
                        model=model_name,
                        messages=messages,
                        tools=None  # No more tools
                    )
                    
                    # Get final content
                    final_content = final_response.get("content", "").strip()
                    if not final_content:
                        logger.warning("[BRAIN] ⚠️ OpenAI returned empty content after tool execution")
                        return "I've completed that task for you!"
                    
                    return final_content
                    
                except Exception as tool_error:
                    logger.error(f"[BRAIN] ❌ Error executing tools: {tool_error}", exc_info=True)
                    return "I tried to perform that action, but ran into an issue. The task might not have completed."
            
            # No tool calls
            content = response.get("content", "").strip()
            if not content:
                logger.warning("[BRAIN] ⚠️ OpenAI returned empty content (no tools)")
                return "I'm not sure how to respond to that. Could you rephrase?"
            
            return content
            
        except Exception as e:
            # Log error
            logger.error(f"[BRAIN] ❌ Error calling OpenAI: {e}", exc_info=True)
            raise e

# Singleton instance
_brain = None

def get_brain() -> Brain:
    """Get the global brain instance"""
    global _brain
    if _brain is None:
        _brain = Brain()
    return _brain
