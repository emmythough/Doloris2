import os
import json
import redis
from rq import Queue
from datetime import datetime

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

try:
    redis_conn = redis.from_url(REDIS_URL)
    # Create queues
    conversation_queue = Queue("conversation", connection=redis_conn)
    dev_brain_queue = Queue("dev_brain", connection=redis_conn)
except Exception as e:
    print(f"Warning: Redis connection failed: {e}")
    redis_conn = None
    conversation_queue = None
    dev_brain_queue = None

def enqueue_job(queue_name: str, job_type: str, payload: dict, trace_id: str):
    """
    Enqueue a job to Redis.
    """
    if not redis_conn:
        print(f"Error: Redis not connected. Cannot enqueue job {trace_id}")
        return None

    job_data = {
        "type": job_type,
        "trace_id": trace_id,
        "payload": payload,
        "enqueued_at": datetime.utcnow().isoformat()
    }

    if queue_name == "conversation":
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Enqueuing job {trace_id} to conversation queue")
        
        job = conversation_queue.enqueue(
            "app.workers.conversation_worker.process_conversation_job",
            job_data,
            job_id=trace_id
        )
        logger.info(f"Job {trace_id} enqueued successfully with ID: {job.id}")
        return job.id
    elif queue_name == "dev_brain":
        job = dev_brain_queue.enqueue(
            "app.dev_brain.worker.process_repair_job",  # Fixed: was app.workers.dev_brain_worker
            job_data,
            job_id=trace_id
        )
        return job.id
    
    return None
