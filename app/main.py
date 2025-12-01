from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.gateway import router as gateway_router
from app.heartbeat import router as heartbeat_router
from app.api.health import router as health_router
from app.api.chat_v2 import router as chat_v2_router  # NEW - Web API
from app.worker_manager import worker_manager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Doloris 5.3 - Ghost in the Machine", version="5.3.0")

# CORS for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(gateway_router, tags=["gateway"])  # Telegram
app.include_router(heartbeat_router, prefix="/heartbeat", tags=["heartbeat"])
app.include_router(health_router, tags=["health"])
app.include_router(chat_v2_router, tags=["web"])  # NEW - Web frontend

@app.on_event("startup")
async def startup_event():
    """Start the embedded worker when the app starts"""
    logger.info("Starting Doloris 5.3 - Ghost in the Machine...")
    worker_manager.start_worker()
    logger.info("All systems online")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the worker when the app shuts down"""
    logger.info("Shutting down...")
    worker_manager.stop_worker()

@app.get("/")
async def root():
    return {
        "status": "online",
        "version": "5.3.0",
        "architecture": "Ghost in the Machine",
        "worker": "embedded"
    }
