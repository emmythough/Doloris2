from app.api.gateway import app
from app.telegram_webhook import router as telegram_router
from app.heartbeat import router as heartbeat_router

# This file is kept for compatibility with Render's start command
# uvicorn app.main:app


app.include_router(telegram_router, prefix="/telegram", tags=["telegram"])
app.include_router(heartbeat_router, prefix="/heartbeat", tags=["heartbeat"])
