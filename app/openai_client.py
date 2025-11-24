import logging
from openai import OpenAI
from app.config import OPENAI_API_KEY
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)

class OpenAIClient:
    """Wrapper for OpenAI API interactions"""
    
    async def chat_completion(
        self,
        messages: List[Dict],
        model: str = "gpt-5-mini",
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Call OpenAI ChatCompletion API.
        Handles new GPT-5 file input format.
        """
        try:
            # Pre-process messages to handle 'input_file' type if present
            # The Brain constructs the message content, but we ensure it's formatted correctly for the API
            formatted_messages = []
            for msg in messages:
                if isinstance(msg.get("content"), list):
                    # Already structured content
                    formatted_messages.append(msg)
                elif "File URL:" in str(msg.get("content", "")):
                    # Detect file URL in text and convert to structured input (if Brain didn't already)
                    # This is a fallback/helper if Brain passes text with URL
                    content_str = msg["content"]
                    parts = content_str.split("File URL: ")
                    if len(parts) > 1:
                        text_part = parts[0].strip()
                        url_part = parts[1].strip()
                        formatted_messages.append({
                            "role": msg["role"],
                            "content": [
                                {"type": "text", "text": text_part},
                                {"type": "input_file", "file_url": url_part}
                            ]
                        })
                    else:
                        formatted_messages.append(msg)
                else:
                    formatted_messages.append(msg)

            logger.info(f"Calling OpenAI with model: {model}")
            
            # Note: This is async in the Brain, but standard OpenAI client is sync.
            # In a real async app, we'd use AsyncOpenAI. For now, we wrap it or assume sync.
            # Since the user's code used `await` in Brain, we should ideally use AsyncOpenAI.
            # But to minimize changes to existing client structure, we'll keep it sync-wrapped or just sync.
            # Wait, the previous client was sync but Brain awaited it? 
            # Let's check the previous file... it didn't have a class structure in the snippet I saw earlier.
            # I will implement it as a class method since Brain calls `self.openai_client.chat_completion`.
            
            # Prepare arguments
            api_args = {
                "model": model,
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
    temperature: float = 0.7
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
        
        if not model.startswith("o1") and not model.startswith("o3"):
            api_args["temperature"] = temperature

        response = client.chat.completions.create(**api_args)
        return response.choices[0].message
    except Exception as e:
        logger.error(f"OpenAI API Error: {e}")
        raise e
