```
# AI FrontDesk

An AI-powered virtual receptionist for medical clinics. Patients can ask questions about the clinic or book appointments through a chat interface.

## What it does

- Answers clinic FAQ questions using uploaded documents (RAG pipeline)
- Books, reschedules, and cancels appointments via Google Calendar
- Multi-turn conversations — remembers context within a session
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

## Project Structure

```
ai-frontdesk/
├── app/
│   ├── agents/        # LangGraph agents (router, FAQ, scheduling, fallback)
│   ├── api/           # FastAPI routes
│   ├── calendar/      # Google Calendar integration
│   └── rag/           # Document ingestion and retrieval
├── sample_data/       # Sample FAQ documents
├── tests/             # Unit tests
├── main.py            # FastAPI entry point
└── streamlit_app.py   # Chat UI
```

## How to Run

**1. Clone and set up environment**
```
git clone https://github.com/Priyall33/AI-Frontdesk-.git
cd AI-Frontdesk-
conda create -n frontdesk python=3.11
conda activate frontdesk
pip install -r requirements.txt
```

**2. Set up environment variables**

Create a `.env` file in the root:
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
```
docker start qdrant
```

**4. Start the API**
```
python -m uvicorn main:app --reload
```

**5. Upload clinic FAQ**

Go to http://localhost:8000/docs and use the /api/ingest endpoint to upload a FAQ document.

**6. Start the chat UI**
```
python -m streamlit run streamlit_app.py
```

## Architecture

```
Patient Message
      │
      ▼
   Router Agent
      │
      ├── intent: faq ──────────► FAQ Agent (searches Qdrant, answers with Groq)
      │
      ├── intent: scheduling ───► Scheduling Agent (extracts entities, books Google Calendar)
      │
      └── intent: out_of_scope ─► Fallback Agent
```
