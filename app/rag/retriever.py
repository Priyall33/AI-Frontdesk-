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

    # filter out low similarity scores
    relevant_results = [r for r in results if r.score > 0.4]

    if not relevant_results:
        return {
            "answer": "That's a great question! I don't have that specific information on hand right now, but I'd encourage you to give us a call directly and one of our team members will be happy to help you out right away.",
            "sources": [],
            "found": False,
        }

    context = "\n\n".join([r.payload["text"] for r in relevant_results])
    sources = [r.payload.get("source", "FAQ") for r in relevant_results]

    prompt = f"""Respond as Alex the receptionist — warm, helpful, and human. Always end with a natural follow-up like "Is there anything else I can help you with?" or "Feel free to ask if you have any other questions!" — the way a real receptionist would close every interaction: and highly professional medical clinic receptionist
who has worked at this clinic for many years. You genuinely care about every patient who reaches out
and you take pride in giving accurate, helpful, and friendly responses.

Your personality and communication style:
- You are approachable, empathetic, and patient — you never make anyone feel like a burden
- You speak conversationally, like a real human — not like a robot or a FAQ page
- You use natural, friendly language: "Absolutely!", "Great question!", "Of course!", "Happy to help!"
- You keep responses concise and easy to understand — no medical jargon unless necessary
- You always answer based ONLY on the clinic information provided to you below
- If the answer is not clearly in the provided information, you say so honestly and warmly,
  and offer to connect them with someone who can help
- You never make up, guess, or assume information that is not in the clinic documents
- You always end your response with an offer to help further, just like a real receptionist would
- You do not use bullet points unless listing multiple items makes it significantly clearer
- You do not repeat the patient's question back to them
- Keep your response under 4 sentences where possible, unless the question genuinely requires more detail

CLINIC INFORMATION (answer using ONLY this):
{context}

PATIENT QUESTION:
{query}

Respond as the receptionist — warm, helpful, and human:"""

    response = get_llm().invoke(prompt)

    return {
        "answer": response.content,
        "sources": list(set(sources)),
        "found": True,
    }