import json
import logging
from typing import Dict, Any
from app.openai_client import openai_client

logger = logging.getLogger(__name__)

class IntentRouter:
    """
    Classifies user intent using a cheap model (gpt-4o-mini).
    """
    
    SYSTEM_PROMPT = """
You are an intent classifier for a personal AI assistant.
Classify the user's message into one of the following intents.
Return ONLY a JSON object.

Intents:
- chat: casual conversation, greetings, questions
- create_task: add todo, reminder, "remind me to..."
- list_tasks: show tasks, "what do I have to do?"
- complete_task: mark task done, "I finished..."
- log_entry: journal, note, "I'm feeling...", "Note that..."
- trace_query: system debugging, "trace id...", "show logs"
- dev_command: /repair, /stats, technical commands

Output Format:
{
  "intent": "intent_name",
  "confidence": 0.0-1.0,
  "entities": { ... extracted data ... }
}
"""

    @staticmethod
    async def classify(text: str) -> Dict[str, Any]:
        try:
            # Use the cheapest model for fast classification
            response = await openai_client.chat_completion(
                messages=[
                    {"role": "system", "content": IntentRouter.SYSTEM_PROMPT},
                    {"role": "user", "content": text}
                ],
                model="gpt-4o-mini",  # Cheapest OpenAI model for classification
                # response_format={"type": "json_object"} # Not supported in wrapper yet, need to handle json parsing manually or update wrapper
            )
            
            # The wrapper returns a dict with 'content'
            content = response.get("content", "{}")
            # Strip markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            result = json.loads(content)
            logger.info(f"Router classified: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Router failed: {e}")
            # Fallback to chat
            return {"intent": "chat", "confidence": 0.0, "entities": {}}
