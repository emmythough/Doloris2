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
        model: str = "gpt-5-mini",
        tools: Optional[List[Dict]] = None,
        temperature: float = 1.0
    ) -> Dict[str, Any]:
        """
        Call OpenAI Responses API.
        Transforms messages to the new input format.
        """
        try:
            # 1. Transform messages to inputs (system -> developer, etc.)
            inputs = []
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                
                # Map 'system' to 'developer' for new API
                if role == "system":
                    role = "developer"
                
                # Handle structured content (files/images)
                if isinstance(content, list):
                    inputs.append({"role": role, "content": content})
                
                # Handle text with potential file URLs (legacy support)
                elif "File URL:" in str(content):
                    parts = content.split("File URL: ")
                    if len(parts) > 1:
                        text_part = parts[0].strip()
                        url_part = parts[1].strip()
                        inputs.append({
                            "role": role,
                            "content": [
                                {"type": "input_text", "text": text_part},
                                {"type": "input_file", "file_url": url_part}
                            ]
                        })
                    else:
                        inputs.append({"role": role, "content": content})
                else:
                    inputs.append({"role": role, "content": content})

            logger.info(f"[OPENAI] 🌐 Calling Responses API with model: {model}")
            logger.info(f"[OPENAI] 📊 Inputs: {len(inputs)} messages")
            if tools:
                logger.info(f"[OPENAI] 🛠️ Tools: {len(tools)} available")
            
            # 2. Prepare arguments
            api_args = {
                "model": model,
                "input": inputs
            }
            
            # Only add tools if they exist and are not empty
            if tools:
                api_args["tools"] = tools
            
            # Don't send temperature parameter at all - GPT-5 is strict about this
            
            # 3. Call Responses API
            logger.info(f"[OPENAI] 📡 Making API call...")
            response = client.responses.create(**api_args)
            
            logger.info(f"[OPENAI] ✅ Response received!")
            
            # 4. Parse output
            content_text = ""
            tool_calls = []
            
            # Try to get text output
            if hasattr(response, 'output_text'):
                content_text = response.output_text
                logger.info(f"[OPENAI] 📝 Content: '{content_text[:100]}...'")
            
            # Parse output items for tool calls
            if hasattr(response, 'output'):
                logger.info(f"[OPENAI] 🔍 Parsing {len(response.output)} output items...")
                for item in response.output:
                    if hasattr(item, 'type') and item.type == "message":
                        if hasattr(item, 'content'):
                            for part in item.content:
                                if hasattr(part, 'type'):
                                    if part.type == "tool_call":
                                        tool_calls.append({
                                            "id": part.id,
                                            "name": part.function.name,
                                            "arguments": part.function.arguments,
                                            "type": "tool_call"
                                        })
                                        logger.info(f"[OPENAI] 🛠️ Tool call: {part.function.name}")
                                    elif part.type == "output_text" and not content_text:
                                        content_text += part.text
            
            logger.info(f"[OPENAI] ✅ Parsed: {len(tool_calls)} tool calls")
            return {
                "content": content_text,
                "tool_calls": tool_calls if tool_calls else None
            }
            
        except Exception as e:
            logger.error(f"OpenAI Responses API Error: {e}", exc_info=True)
            return {"content": f"I encountered an error: {str(e)}"}

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
