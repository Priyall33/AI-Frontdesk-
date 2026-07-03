from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    EMBEDDING_MODEL,
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_COLLECTION,
    CLINIC_ID,
)

_embeddings = None
_client = None
_llm = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return _embeddings

def get_client():
    global _client
    if _client is None:
        _client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    return _client

def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(api_key=GROQ_API_KEY, model_name=GROQ_MODEL, temperature=0.2)
    return _llm

def search_faq(query: str, clinic_id: str = CLINIC_ID, top_k: int = 3):
    query_vector = get_embeddings().embed_query(query)
    
    clinic_filter = Filter(
        must=[FieldCondition(key="clinic_id", match=MatchValue(value=clinic_id))]
    )
    
    results = get_client().search(
        collection_name=QDRANT_COLLECTION,
        query_vector=query_vector,
        query_filter=clinic_filter,
        limit=top_k,
    )
    return results

def answer_question(query: str, clinic_id: str = CLINIC_ID):
    
    results = search_faq(query, clinic_id)
    
    # filter out low similarity score 
    relevant_results = [r for r in results if r.score > 0.4]
    
    if not relevant_results:
        return {
            "answer": "I don't have that information available. Would you like me to have someone from the clinic call you back?",
            "sources": [],
            "found": False,
        }
    
    context = "\n\n".join([r.payload["text"] for r in relevant_results])
    sources = [r.payload.get("source", "FAQ") for r in relevant_results]
    
    prompt = f"""You are a helpful clinic receptionist assistant.
Answer the patient's question using ONLY the information provided below.
If the answer is not in the provided information, say you don't have that information.
Do NOT make up or guess any information.

CLINIC INFORMATION:
{context}

PATIENT QUESTION:
{query}

ANSWER:"""
    
    response = get_llm().invoke(prompt)
    
    return {
        "answer": response.content,
        "sources": list(set(sources)),
        "found": True,
    }