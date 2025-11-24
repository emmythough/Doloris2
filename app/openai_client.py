import logging
from openai import OpenAI
from app.config import OPENAI_API_KEY
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)

class OpenAIClient:
    """Wrapper for OpenAI API interactions"""
                "messages": formatted_messages,
                "tools": tools
            }
            
            # Reasoning models (o1, o3) do not support temperature (or require it to be 1)
            # We exclude it for them to be safe.
            if not model.startswith("o1") and not model.startswith("o3"):
                api_args["temperature"] = temperature
            
            response = client.chat.completions.create(**api_args)
            
            message = response.choices[0].message
            
            return {
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                        "type": "tool_call" # Add type for ToolsOrchestrator
                    } for tc in message.tool_calls
                ] if message.tool_calls else None
            }
            
        except Exception as e:
            logger.error(f"OpenAI API Error: {e}")
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
    Returns the raw OpenAI message object (not async).
    """
    try:
        # Prepare arguments
        api_args = {
            "model": model,
            "messages": messages,
            "tools": tools
        }
        
        if temperature != 1.0 and not model.startswith("o1") and not model.startswith("o3"):
            api_args["temperature"] = temperature

        response = client.chat.completions.create(**api_args)
        return response.choices[0].message
    except Exception as e:
        logger.error(f"OpenAI API Error: {e}")
        raise e
