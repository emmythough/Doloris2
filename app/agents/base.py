from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging
import json
from app.openai_client import openai_client
from app.tools import execute_tool

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Base class for all domain agents.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.model = "gpt-4o-mini" # Default to mini
        
    @abstractmethod
    def get_system_prompt(self) -> str:
        pass
    
    @abstractmethod
    def get_tools(self) -> List[Dict]:
        pass
        
    MAX_TOKENS = 2048
    MAX_TOOL_CALLS = 3

    async def run(self, user_message: str, context: Dict = None, history: List[Dict] = None) -> str:
        """
        Main execution loop for the agent.
        1. Build messages (System + Context + History + User)
        2. Call LLM
        3. Handle Tools (if any)
        4. Return final response
        """
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
        ]
        
        # Add context if provided (e.g. recent tasks)
        if context:
            context_str = f"Context:\n{json.dumps(context, indent=2)}"
            messages.append({"role": "system", "content": context_str})
            
        # Add conversation history
        if history:
            messages.extend(history)
            
        messages.append({"role": "user", "content": user_message})
        
        tool_calls_count = 0
        
        try:
            while tool_calls_count < self.MAX_TOOL_CALLS:
                # Call LLM
                response = await openai_client.chat_completion(
                    messages=messages,
                    model=self.model,
                    tools=self.get_tools(),
                    # max_tokens=self.MAX_TOKENS # Not supported in wrapper yet, need to add
                )
                
                # Parse response correctly - openai_client returns {content, tool_calls} directly
                content = response.get("content")
                tool_calls = response.get("tool_calls")
                
                # If no tool calls, we are done
                if not tool_calls:
                    return content or ""
                
                # If we have tool calls, execute them
                # Reconstruct message for history
                assistant_message = {
                    "role": "assistant",
                    "content": content,
                    "tool_calls": tool_calls
                }
                messages.append(assistant_message) # Add assistant's tool call message to history
                
                logger.info(f"Agent {self.__class__.__name__} calling tools: {len(tool_calls)}")
                
                for tool_call in tool_calls:
                    function_name = tool_call.get("function", {}).get("name")
                    arguments_str = tool_call.get("function", {}).get("arguments")
                    tool_call_id = tool_call.get("id")
                    
                    try:
                        arguments = json.loads(arguments_str)
                        result = execute_tool(function_name, arguments, self.user_id)
                    except Exception as e:
                        result = f"Error executing tool {function_name}: {str(e)}"
                        
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": str(result)
                    })
                
                tool_calls_count += 1
                
                # Loop continues to send tool outputs back to LLM

            return "I reached my tool call limit. Please try a simpler request."
            
        except Exception as e:
            logger.error(f"Agent run failed: {e}")
            return "I'm sorry, I encountered an error processing your request."
