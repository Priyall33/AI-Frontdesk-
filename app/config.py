import os
from dotenv import load_dotenv

load_dotenv()

# Groq (LLM)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# HuggingFace (embeddings)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Qdrant (vector database)
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "clinic_faqs")

# App
CLINIC_ID = os.getenv("CLINIC_ID", "clinic_001")
APP_ENV = os.getenv("APP_ENV", "development")