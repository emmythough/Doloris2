from fastapi import FastAPI
from app.telegram_webhook import router as telegram_router
from app.heartbeat import router as heartbeat_router

app = FastAPI(title="Doloris 2 AI Assistant")

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Doloris 2 is alive"}

app.include_router(telegram_router, prefix="/telegram", tags=["telegram"])
app.include_router(heartbeat_router, prefix="/heartbeat", tags=["heartbeat"])
