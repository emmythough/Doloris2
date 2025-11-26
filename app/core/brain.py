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
