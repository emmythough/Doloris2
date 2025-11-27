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
    
    logger.info(f"Processing job for trace {trace_id}")
    
    try:
        # Log Start
        system_logger.log_event(trace_id, "worker", "worker_start", "info", {"job_type": job_data.get("type")})
        
        # 1. Call Intent Router
        # We need to run async code in sync worker, so we use asyncio.run or similar if possible, 
        # but RQ workers are sync. Ideally we should use async worker or run_until_complete.
        # For simplicity in this sync worker, we might need a sync wrapper or just use asyncio.run.
        import asyncio
        from app.brain.router import IntentRouter
        from app.agents.chat import ChatAgent
        from app.agents.tasks import TasksAgent
        from app.agents.dev import DevCoordinatorAgent
        
        raw_update = payload.get("raw_update", {})
        message_text = raw_update.get("message", {}).get("text", "")
        user_id = str(raw_update.get("message", {}).get("from", {}).get("id", ""))
        
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
        from app.db import DB
        
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
        asyncio.run(TelegramClient.send_message(user_id, response_text))
        logger.info(f"Sent response to {user_id}")
        
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
