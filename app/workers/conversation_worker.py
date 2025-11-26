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

        # 2. Dispatch to Agent
        agent = None
        if intent == "create_task" or intent == "list_tasks":
            agent = TasksAgent(user_id)
        elif intent == "dev_command":
            agent = DevCoordinatorAgent(user_id)
        else:
            agent = ChatAgent(user_id)
            
        # Run Agent
        response_text = asyncio.run(agent.run(message_text))
        logger.info(f"Trace {trace_id} - Agent Response: {response_text[:50]}...")
        
        system_logger.log_event(trace_id, "worker", "agent_response", "info", {"response_length": len(response_text)})

        # 3. Send Response via Telegram API
        from app.channels.telegram import TelegramClient
        asyncio.run(TelegramClient.send_message(user_id, response_text))
        logger.info(f"Sent response to {user_id}")
        
        # Log Completion
        system_logger.log_event(trace_id, "worker", "worker_complete", "success", {"status": "success"})
        
    except Exception as e:
        logger.error(f"Error processing job {trace_id}: {e}", exc_info=True)
        system_logger.log_event(trace_id, "worker", "worker_error", "error", {"error": str(e)})
        # Don't raise if we want to avoid retrying forever on bad logic
        # raise e

if __name__ == "__main__":
    # Standalone worker script
    conn = redis.from_url(REDIS_URL)
    qs = ['conversation']
    w = Worker(qs, connection=conn)
    w.work()
