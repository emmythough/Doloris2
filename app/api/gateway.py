from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from app.core.queue import enqueue_job
from app.core.system_logger import system_logger
import uuid
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/telegram/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Non-blocking webhook handler.
    1. Generates trace_id
    2. Enqueues job to Redis
    3. Returns 200 OK immediately
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Generate Trace ID
    trace_id = f"tr_{uuid.uuid4().hex[:8]}"
    
    # Log Ingestion Event
    system_logger.log_event(
        trace_id=trace_id,
        component="gateway",
        event_type="telegram_in",
        status="info",
        details={"payload_size": len(str(payload))}
    )

    # Extract basic info for the queue payload
    # We pass the full payload to the worker to handle parsing
    job_payload = {
        "raw_update": payload,
        "source": "telegram"
    }

    # Enqueue Job (using BackgroundTasks to ensure we return 200 OK fast, 
    # though Redis enqueue is fast enough to do synchronously usually)
    # We'll do it synchronously here to ensure it's in Redis before we say OK.
    try:
        job_id = enqueue_job(
            queue_name="conversation",
            job_type="process_update",
            payload=job_payload,
            trace_id=trace_id
        )
        logger.info(f"Enqueued job {job_id} for trace {trace_id}")
    except Exception as e:
        logger.error(f"Failed to enqueue job: {e}")
        # In a real prod system, we might want to fallback or return 500, 
        # but for Telegram we should return 200 to stop retries if it's a permanent error.
        # However, if Redis is down, we might want to retry. 
        # For now, let's return 200 and log error.
        return {"status": "error", "message": "Internal queue error"}

    return {"status": "ok", "trace_id": trace_id}
