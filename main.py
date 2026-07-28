from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import CLINIC_ID, APP_ENV
from app.api.routes import router 
from fastapi import WebSocket 
from app.voice.pipeline import run_voice_pipeline
from app.logger import logger

app = FastAPI(
    title="AI FrontDesk",
    description="Multi-agent patient assistant with RAG and Google Calendar scheduling",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit UI 
    allow_methods=["POST", "GET"],
    allow_headers=["x-api-key", "Content-Type"],
)

app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "AI FrontDesk",
        "clinic_id": CLINIC_ID,
        "env": APP_ENV,
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.websocket("/ws/voice/{session_id}")
async def voice_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        await run_voice_pipeline(websocket, session_id)
    except Exception as e:
        logger.error(f"VOICE ERROR | session={session_id} | {e}")