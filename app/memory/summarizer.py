from typing import List, Dict
from app.openai_client import openai_client
import logging

logger = logging.getLogger(__name__)

class RollingSummarizer:
    """
    Compresses conversation history to maintain context within token limits.
    """
    
    MAX_HISTORY_LENGTH = 10
    
    @staticmethod
    async def summarize(messages: List[Dict]) -> List[Dict]:
        """
        Summarize the conversation if it exceeds the max length.
        Keeps the system prompt and the last N messages, summarizing the middle.
        """
        if len(messages) <= RollingSummarizer.MAX_HISTORY_LENGTH:
            return messages
            
        # Identify parts
        system_prompt = messages[0] if messages and messages[0]["role"] == "system" else None
        start_index = 1 if system_prompt else 0
        
        # We want to keep the last 5 messages intact
        keep_count = 5
        to_summarize = messages[start_index:-keep_count]
        recent_history = messages[-keep_count:]
        
        if not to_summarize:
            return messages
            
        # Generate summary
        text_to_summarize = "\n".join([f"{m['role']}: {m.get('content', '')}" for m in to_summarize])
        
        try:
            summary_response = await openai_client.chat_completion(
                messages=[
                    {"role": "system", "content": "Summarize the following conversation history concisely, preserving key details, tasks, and user preferences."},
                    {"role": "user", "content": text_to_summarize}
                ],
                model="gpt-4o-mini"
            )
            summary_text = summary_response.get("message", {}).get("content", "")
            
            # Construct new history
            new_history = []
            if system_prompt:
                new_history.append(system_prompt)
            
            new_history.append({
                "role": "system", 
                "content": f"Previous conversation summary: {summary_text}"
            })
            
            new_history.extend(recent_history)
            
            logger.info(f"Summarized {len(to_summarize)} messages into one summary block.")
            return new_history
            
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return messages # Fallback to full history
