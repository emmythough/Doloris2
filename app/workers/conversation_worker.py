import json
import logging
import os
import redis
from rq import Worker, Queue
from app.core.system_logger import system_logger

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

def process_conversation_job(job_data):
    """
    Process a conversation job from the queue.
    This is the main entry point for the worker.
    """
    trace_id = job_data.get("trace_id")
    payload = job_data.get("payload")
    
    logger.info(f"Processing job for trace {trace_id} - WORKER VERSION: 3.0.2 (Fixed syntax)")
    
    try:
        # Log Start
        system_logger.log_event(trace_id, "worker", "worker_start", "info", {"job_type": job_data.get("type")})
        
        # 1. Call Intent Router
        import asyncio
        from app.brain.router import IntentRouter
        from app.agents.chat import ChatAgent
        from app.agents.tasks import TasksAgent
        from app.agents.dev import DevCoordinatorAgent
        from app.db import DB
        
        raw_update = payload.get("raw_update", {})
        message_text = raw_update.get("message", {}).get("text", "")
        
        # Extract Telegram user info
        telegram_user_id = raw_update.get("message", {}).get("from", {}).get("id")
        user_name = raw_update.get("message", {}).get("from", {}).get("first_name", "Unknown")
        
        # Get or create user and get their UUID
        user = DB.get_or_create_user(telegram_user_id, user_name)
        user_id = user.id  # This is the UUID we need for database queries
        
        if not message_text:
            logger.warning(f"No text in message for trace {trace_id}")
            return

        # Run async classification
        intent_result = asyncio.run(IntentRouter.classify(message_text))
        intent = intent_result.get("intent", "chat")
        logger.info(f"Trace {trace_id} - Intent: {intent}")
        
        system_logger.log_event(trace_id, "worker", "intent_classified", "info", intent_result)

        # 1.5 Retrieve Context & History
        from app.memory.retrieval import ContextRetriever
        from app.memory.summarizer import RollingSummarizer
        
        # Context (Tasks, Logs)
        context = ContextRetriever.get_context(user_id)
        
        # History (Recent Messages)
        # Fetch last 20 messages
        raw_history = DB.get_recent_messages(user_id, limit=20)
        # Convert to Dict format for LLM
        history_dicts = [{"role": m.role, "content": m.content} for m in raw_history]
        
        # Summarize if needed
        # Note: We run this async
        summarized_history = asyncio.run(RollingSummarizer.summarize(history_dicts))
        
        # 2. Dispatch to Agent
        agent = None
        if intent == "create_task" or intent == "list_tasks" or intent == "complete_task":
            agent = TasksAgent(user_id)
        elif intent == "log_entry":
            from app.agents.notes import NotesAgent
            agent = NotesAgent(user_id)
        elif intent == "trace_query":
            from app.agents.system import SystemAgent
            agent = SystemAgent(user_id)
        elif intent == "dev_command":
            agent = DevCoordinatorAgent(user_id)
        else:
            agent = ChatAgent(user_id)
            
        # Run Agent with Context & History
        response_text = asyncio.run(agent.run(message_text, context=context, history=summarized_history))
        logger.info(f"Trace {trace_id} - Agent Response: {response_text[:50]}...")
        
        system_logger.log_event(trace_id, "worker", "agent_response", "info", {"response_length": len(response_text)})

        # 3. Send Response via Telegram API
        from app.channels.telegram import TelegramClient
        # Use the Telegram chat ID, not the database UUID
        telegram_chat_id = raw_update.get("message", {}).get("chat", {}).get("id")
        
        telegram_send_success = False
        try:
            asyncio.run(TelegramClient.send_message(telegram_chat_id, response_text))
            logger.info(f"Sent response to Telegram chat {telegram_chat_id}")
            telegram_send_success = True
        except Exception as telegram_error:
            logger.error(f"Failed to send Telegram message: {telegram_error}")
            system_logger.log_event(
                trace_id, 
                "worker", 
                "telegram_send_failed", 
                "error", 
                {"error": str(telegram_error), "chat_id": telegram_chat_id}
            )
            # Don't fail the whole job just because Telegram send failed
        
        # Only log success if it actually succeeded
        if telegram_send_success:
            system_logger.log_event(trace_id, "worker", "telegram_sent", "success", {"chat_id": telegram_chat_id})
        
        # Log Completion
        system_logger.log_event(trace_id, "worker", "worker_complete", "success", {"status": "success"})
        
    except Exception as e:
        import traceback
        error_details = {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "job_type": job_data.get("type"),
            "failed_step": "unknown" # Could refine this with more granular try/except blocks if needed
        }
        logger.error(f"Error processing job {trace_id}: {e}", exc_info=True)
        system_logger.log_event(trace_id, "worker", "worker_error", "error", error_details)
        # Don't raise if we want to avoid retrying forever on bad logic
        # raise e

if __name__ == "__main__":
    # Standalone worker script
    conn = redis.from_url(REDIS_URL)
    qs = ['conversation']
    w = Worker(qs, connection=conn)
    w.work()
