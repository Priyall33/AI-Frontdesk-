from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from pydantic import BaseModel
import shutil, os
from app.rag.ingestor import ingest_file
from app.agents.graph import run_agent
from app.agents.memory import (get_history, update_history, get_entities, update_entities, get_session_intent, update_session_intent)
from app.config import CLINIC_ID, API_KEY
from app.logger import logger

router = APIRouter()
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

class ChatRequest(BaseModel):
    message: str
    clinic_id: str = CLINIC_ID
    session_id: str = "default"

@router.post("/ingest")
async def ingest_faq(file: UploadFile = File(...), x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    allowed = [".pdf", ".txt", ".docx", ".csv", ".xlsx"]
    safe_filename = os.path.basename(file.filename)
    ext = os.path.splitext(safe_filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"File type {ext} not supported")
    temp_path = os.path.join(UPLOAD_DIR, safe_filename)
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    count = ingest_file(temp_path)
    os.remove(temp_path)
    logger.info(f"INGEST | file={safe_filename} | chunks={count}")
    return {"status": "success", "filename": safe_filename, "chunks_stored": count}

@router.post("/chat")
async def chat(request: ChatRequest, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    history = get_history(request.session_id)
    entities = get_entities(request.session_id)
    previous_intent = get_session_intent(request.session_id)
    result = run_agent(message=request.message, session_id=request.session_id, clinic_id=request.clinic_id, chat_history=history, entities=entities, previous_intent=previous_intent)
    update_history(request.session_id, "patient", request.message)
    update_history(request.session_id, "assistant", result["answer"])
    update_session_intent(request.session_id, result["intent"] or "")
    if result.get("entities") is not None:
        update_entities(request.session_id, result["entities"])
    logger.info(f"CHAT | session={request.session_id} | intent={result['intent']} | message={request.message[:50]}")
    return {"answer": result["answer"], "intent": result["intent"], "sources": result["sources"], "found": result["found"], "session_id": request.session_id}