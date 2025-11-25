"""
Doloris Brain - Main conversation orchestrator

        
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
