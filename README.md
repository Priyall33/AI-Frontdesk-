# AI FrontDesk

An AI-powered virtual receptionist for medical clinics. Patients can ask questions about the clinic or book appointments through a chat interface.

## What it does

- Answers clinic FAQ questions using uploaded documents (RAG pipeline)
- Books appointments via Google Calendar
- Maintains scheduling context across a conversation using session memory 
- Routes messages intelligently between agents using LangGraph

## Tech Stack

| Layer | Tool |
|-------|------|
| LLM | Groq (LLaMA 3.1 8B) |
| Embeddings | HuggingFace sentence-transformers |
| Vector DB | Qdrant |
| Agent Orchestration | LangGraph |
| Backend API | FastAPI |
| Calendar | Google Calendar API |
| Chat UI | Streamlit |

## How to Run

**1. Clone and set up**
```bash
git clone https://github.com/Priyall33/AI-Frontdesk-.git
cd AI-Frontdesk-
conda create -n frontdesk python=3.11
conda activate frontdesk
pip install -r requirements.txt
```

**2. Create a `.env` file in the root**
```
GROQ_API_KEY=your-groq-key
GROQ_MODEL=llama-3.1-8b-instant
EMBEDDING_MODEL=all-MiniLM-L6-v2
QDRANT_HOST=localhost
QDRANT_PORT=6333
CLINIC_ID=clinic_001
APP_ENV=development
```

**3. Start Qdrant**
```bash
docker start qdrant
```

**4. Start the API**
```bash
python -m uvicorn main:app --reload
```

**5. Upload clinic FAQ**

Go to `http://localhost:8000/docs` and use `/api/ingest` to upload a FAQ document.

**6. Start the chat UI**
```bash
python -m streamlit run streamlit_app.py
```

## Architecture

```
Patient Message → Router Agent
                      ├── faq         → FAQ Agent (Qdrant + Groq)
                      ├── scheduling  → Scheduling Agent (Google Calendar)
                      └── out_of_scope → Fallback Agent
```
