"""
Intent Classifier - Fast intent detection using gpt-5-nano

Classifies user messages into:
- task: Task/reminder management
- chat: General conversation
- file: File-related query
- admin: Admin/repair commands
- note: Note-taking

Also detects admin commands like /repair, /selfcheck, "diagnose yourself"
"""

import logging
import json
from typing import Dict, Optional
from app.openai_client import OpenAIClient
from app.config import GPT_5_NANO_MODEL

logger = logging.getLogger(__name__)

class IntentClassifier:
    """Fast intent detection using gpt-5-nano for routing"""
    
    SYSTEM_PROMPT = """You are an intent classifier for Doloris, a personal AI assistant.

Classify user messages into ONE of these intents:
- "task" - Managing tasks, reminders, to-dos
- "chat" - General conversation, questions, casual talk
- "file" - Questions about files, document analysis
- "admin" - Admin commands, system diagnostics, repair requests
- "note" - Creating, managing notes

Admin commands include:
- /repair
- /selfcheck
- "diagnose yourself"
- "check for errors"
- "fix yourself"
- "investigate [issue]"

Respond ONLY with JSON in this exact format:
{"intent": "task|chat|file|admin|note", "command": "/repair" or null, "confidence": 0.0-1.0}

Examples:
User: "Remind me to call mom tomorrow"
{"intent": "task", "command": null, "confidence": 0.95}

User: "How are you?"
{"intent": "chat", "command": null, "confidence": 0.90}

User: "/repair"
{"intent": "admin", "command": "/repair", "confidence": 1.0}

User: "Diagnose recent failures"
{"intent": "admin", "command": "diagnose", "confidence": 0.85}

User: "Note: Project deadline moved"
{"intent": "note", "command": null, "confidence": 0.92}"""
    
    def __init__(self):
        self.client = OpenAIClient()
    
    async def classify(self, message: str) -> Dict[str, any]:
        """
        Classify user intent and detect admin commands
        
        Args:
            message: User's message text
        
        Returns:
            {
                "intent": "task|chat|file|admin|note",
                "command": "/repair" or None,
                "confidence": 0.0-1.0
            }
        """
        logger.info(f"[INTENT] Classifying: '{message[:50]}...'")
        
        try:
            # Use gpt-5-nano for fast classification
            response = await self.client.chat_completion(
                model=GPT_5_NANO_MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": message}
                ],
                tools=None  # No tools for classification
            )
            
            # Parse JSON response
            content = response.get("content", "{}")
            
            try:
                result = json.loads(content)
                
                # Validate structure
                if "intent" not in result:
                    logger.warning(f"[INTENT] Missing intent in response: {content}")
                    return {"intent": "chat", "command": None, "confidence": 0.5}
                
                logger.info(f"[INTENT] Classified as: {result['intent']} (confidence: {result.get('confidence', 'unknown')})")
                
                if result.get("command"):
                    logger.info(f"[INTENT] Detected admin command: {result['command']}")
                
                return result
                
            except json.JSONDecodeError:
                logger.error(f"[INTENT] Failed to parse JSON: {content}")
                # Fallback: simple keyword detection
                return self._fallback_classification(message)
        
        except Exception as e:
            logger.error(f"[INTENT] Classification error: {e}", exc_info=True)
            # Fallback to keyword-based classification
            return self._fallback_classification(message)
    
    def _fallback_classification(self, message: str) -> Dict[str, any]:
        """
        Fallback classification using simple keyword matching
        Used when gpt-5-nano fails
        """
        message_lower = message.lower()
        
        # Admin commands
        admin_keywords = ["/repair", "/selfcheck", "diagnose", "fix yourself", "check errors", "investigate"]
        if any(keyword in message_lower for keyword in admin_keywords):
            command = next((kw for kw in admin_keywords if kw in message_lower), None)
            return {"intent": "admin", "command": command, "confidence": 0.7}
        
        # Task keywords
        task_keywords = ["remind", "task", "todo", "schedule", "deadline"]
        if any(keyword in message_lower for keyword in task_keywords):
            return {"intent": "task", "command": None, "confidence": 0.6}
        
        # Note keywords
        note_keywords = ["note:", "remember:", "save this", "write down"]
        if any(keyword in message_lower for keyword in note_keywords):
            return {"intent": "note", "command": None, "confidence": 0.6}
        
        # File keywords
        file_keywords = ["file", "document", "pdf", "attachment"]
        if any(keyword in message_lower for keyword in file_keywords):
            return {"intent": "file", "command": None, "confidence": 0.6}
        
        # Default to chat
        return {"intent": "chat", "command": None, "confidence": 0.5}

# Singleton instance
_intent_classifier = None

def get_intent_classifier() -> IntentClassifier:
    """Get the global intent classifier instance"""
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier()
    return _intent_classifier
