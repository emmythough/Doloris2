from fastapi import FastAPI
from app.api.gateway import router as gateway_router
from app.heartbeat import router as heartbeat_router
from app.api.health import router as health_router # Added import for health router
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Doloris 3.0", version="3.0.0")

# Include Routers
app.include_router(gateway_router, tags=["gateway"])
app.include_router(heartbeat_router, prefix="/heartbeat", tags=["heartbeat"])
app.include_router(health_router, prefix="/health", tags=["health"]) # Registered health router

@app.get("/")
async def root():
    return {"status": "online", "version": "3.0.0"}
