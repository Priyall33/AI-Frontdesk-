 # main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import CLINIC_ID, APP_ENV

# Creates your web application
app = FastAPI(
    title="AI FrontDesk",
    description="Multi-agent patient assistant with RAG and Google Calendar scheduling",
    version="0.1.0",
)

# Allows your Streamlit frontend (different port) to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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