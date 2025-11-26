import logging
from openai import OpenAI
from app.config import OPENAI_API_KEY
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)

class OpenAIClient:
    """Wrapper for OpenAI Responses API"""
    
    async def chat_completion(
        self,
        messages: List[Dict],
        model: str = "gpt-4o",
        tools: Optional[List[Dict]] = None,
        temperature: float = 1.0
    ) -> Dict[str, Any]:
        """
        Call OpenAI Chat Completions API.
        Standard implementation supporting tools.
        """
        try:
            logger.info(f"[OPENAI] 🌐 Calling Chat Completions API with model: {model}")
            
            # Prepare arguments
            api_args = {
                "model": model,
                "messages": messages,
                "temperature": temperature
            }
            
            if tools:
                api_args["tools"] = tools
                logger.info(f"[OPENAI] 🛠️ Tools: {len(tools)} available")
            
            # Call API
            logger.info(f"[OPENAI] 📡 Making API call...")
            response = client.chat.completions.create(**api_args)
            
            logger.info(f"[OPENAI] ✅ Response received!")
            
            message = response.choices[0].message
            content_text = message.content or ""
            tool_calls = []
            
            if message.tool_calls:
                for tc in message.tool_calls:
                    tool_calls.append({
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                        "type": "tool_call"
                    })
                    logger.info(f"[OPENAI] 🛠️ Tool call: {tc.function.name}")
            
            logger.info(f"[OPENAI] ✅ Final result: {len(content_text)} chars, {len(tool_calls)} tool calls")
            
            return {
                "content": content_text,
                "tool_calls": tool_calls if tool_calls else None
            }
            
        except Exception as e:
            logger.error(f"OpenAI API Error: {e}", exc_info=True)
            # Return a safe error response structure
            return {"content": "I encountered an error connecting to my brain."}

# Backward-compatible wrapper for legacy code (heartbeat.py)
def get_completion(
    messages: list,
    tools: list = None,
    model: str = "gpt-4o",
    temperature: float = 1.0
):
    """
    Legacy wrapper for backward compatibility.
    Uses old Chat Completions API.
    """
    try:
        api_args = {
            "model": model,
            "messages": messages,
        }
        
        if tools:
            api_args["tools"] = tools
        
        # Only add temperature if not default and not reasoning model
        if temperature != 1.0 and not model.startswith("o1") and not model.startswith("o3"):
            api_args["temperature"] = temperature

        response = client.chat.completions.create(**api_args)
        return response.choices[0].message
    except Exception as e:
        logger.error(f"OpenAI API Error: {e}")
        raise e

# Global instance
openai_client = OpenAIClient()
