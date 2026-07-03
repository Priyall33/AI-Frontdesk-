from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import shutil
import os
from app.rag.ingestor import ingest_file
from app.agents.graph import run_agent  #import graph runner instead of retriever
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
    
    #will run the full multi-agent graph instead of calling retriever directly
    result = run_agent(
        message=request.message,
        session_id=request.session_id,
        clinic_id=request.clinic_id,
    )
    
    return {
        "answer": result["answer"],
        "intent": result["intent"],    #will show what the router decided
        "sources": result["sources"],
        "found": result["found"],
        "session_id": result["session_id"],
    }