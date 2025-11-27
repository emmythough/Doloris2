from fastapi import APIRouter, Response
from app.db import DB
import redis
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

@router.get("/health")
async def health_check():
    """
    Deep health check.
    Verifies:
    1. API is responsive
    2. Redis is reachable
    3. Database is reachable
    """
    status = {
        "api": "ok",
        "redis": "unknown",
        "db": "unknown"
    }
    
    # Check Redis
    try:
        r = redis.from_url(REDIS_URL)
        r.ping()
        status["redis"] = "ok"
    except Exception as e:
        status["redis"] = f"error: {str(e)}"
        logger.error(f"Health check failed (Redis): {e}")

    # Check DB
    try:
        # Simple query to check connection
        DB.supabase.table("users").select("count", count="exact").limit(1).execute()
        status["db"] = "ok"
    except Exception as e:
        status["db"] = f"error: {str(e)}"
        logger.error(f"Health check failed (DB): {e}")
        
    # Determine overall status
    if status["redis"] == "ok" and status["db"] == "ok":
        return status
    else:
        return Response(content=str(status), status_code=503, media_type="application/json")

@router.get("/heartbeat")
async def heartbeat():
    """Simple liveness probe"""
    return {"status": "alive"}
