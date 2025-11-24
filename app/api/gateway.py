"""
API Gateway - Main entry point for Doloris 2.0

Routes requests to appropriate endpoints.
"""

from fastapi import FastAPI
from app.api.endpoints import message, file, tools
from app.telegram_webhook import router as telegram_router
from app.heartbeat import router as heartbeat_router

app = FastAPI(title="Doloris 2.0 API")

# Include routers
app.include_router(message.router, prefix="/api/v1", tags=["messages"])
app.include_router(file.router, prefix="/api/v1", tags=["files"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["tools"])
app.include_router(telegram_router, prefix="/telegram", tags=["telegram"])
app.include_router(heartbeat_router, prefix="/heartbeat", tags=["heartbeat"])

@app.get("/")
async def root():
    return {"status": "online", "version": "2.0", "system": "Doloris Core"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
