from fastapi import FastAPI
from app.api.gateway import router as gateway_router
from app.heartbeat import router as heartbeat_router
from app.api.health import router as health_router
from app.worker_manager import worker_manager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Doloris 3.0", version="3.0.0")

# Include Routers
app.include_router(gateway_router, tags=["gateway"])
app.include_router(heartbeat_router, prefix="/heartbeat", tags=["heartbeat"])
app.include_router(health_router, tags=["health"])

@app.on_event("startup")
async def startup_event():
    """Start the embedded worker when the app starts"""
    logger.info("Starting Doloris 3.0...")
    worker_manager.start_worker()
    logger.info("All systems online")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the worker when the app shuts down"""
    logger.info("Shutting down...")
    worker_manager.stop_worker()

@app.get("/")
async def root():
    return {"status": "online", "version": "3.0.0", "worker": "embedded"}
