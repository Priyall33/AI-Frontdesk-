from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import shutil
import os
from app.rag.ingestor import ingest_file
from app.agents.graph import run_agent
from app.agents.memory import get_history, update_history, get_entities, update_entities
from app.config import CLINIC_ID

router = APIRouter()
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ChatRequest(BaseModel):
    message: str
    clinic_id: str = CLINIC_ID
    session_id: str = "default"


@router.post("/ingest")
async def ingest_faq(file: UploadFile = File(...)):
    allowed = [".pdf", ".txt", ".docx", ".csv"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"File type {ext} not supported")
    temp_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    count = ingest_file(temp_path)
    os.remove(temp_path)
    return {"status": "success", "filename": file.filename, "chunks_stored": count}


@router.post("/chat")
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # load existing history and entities for this session
    history = get_history(request.session_id)
    entities = get_entities(request.session_id)

    # run the agent graph with session context
    result = run_agent(
        message=request.message,
        session_id=request.session_id,
        clinic_id=request.clinic_id,
        chat_history=history,
        entities=entities,
    )

    # save the new messages to session memory
    update_history(request.session_id, "patient", request.message)
    update_history(request.session_id, "assistant", result["answer"])

    # save any partially collected entities for multi-turn scheduling
    if result.get("entities") is not None:
        update_entities(request.session_id, result["entities"])

    return {
        "answer": result["answer"],
        "intent": result["intent"],
        "sources": result["sources"],
        "found": result["found"],
        "session_id": request.session_id,
    }