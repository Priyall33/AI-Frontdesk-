# app/config.py

import os
from dotenv import load_dotenv

# Reads your .env file and loads all variables into the environment
load_dotenv()

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# Qdrant (vector database)
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "clinic_faqs")

# App
CLINIC_ID = os.getenv("CLINIC_ID", "clinic_001")
APP_ENV = os.getenv("APP_ENV", "development")

# Commented out for now — uncomment tomorrow when you have the real API key
# if not OPENAI_API_KEY:
#     raise ValueError("OPENAI_API_KEY is not set. Add it to your .env file.")
