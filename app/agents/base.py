from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging
import json
from app.openai_client import openai_client

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
        
    async def run(self, user_message: str, context: Dict = None) -> str:
        """
        Main execution loop for the agent.
        1. Build messages (System + Context + User)
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
            
        messages.append({"role": "user", "content": user_message})
        
        try:
            # Initial Call
            response = await openai_client.chat_completion(
                messages=messages,
                model=self.model,
                tools=self.get_tools()
            )
            
            # TODO: Handle Tool Calls Loop (simplified for now)
            # If response.tool_calls:
            #   results = execute_tools(response.tool_calls)
            #   messages.append(response.message)
            #   messages.append(tool_outputs)
            #   response = await OpenAIClient.get_chat_completion(...)
            
            return response.get("content", "")
            
        except Exception as e:
            logger.error(f"Agent run failed: {e}")
            return "I'm sorry, I encountered an error processing your request."
