
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

# setting up connections 
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model_name=GROQ_MODEL,
    temperature=0.2, #low temp will be more factual 
)

def search_faq(query: str, clinic_id: str = CLINIC_ID, top_k: int = 3): 
    
    query_vector = embeddings.embed_query(query) # convert question to numbers
    
    # only search chunks that belong to this clinic
    clinic_filter = Filter(
        must=[
            FieldCondition(
                key="clinic_id",
                match=MatchValue(value=clinic_id)
            )
        ]
    )
    
    # search most similar chunks
    results = client.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=query_vector,
        query_filter=clinic_filter,
        limit=top_k, # return top 3 most relevant chunks
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
    
    response = llm.invoke(prompt)
    
    return {
        "answer": response.content,
        "sources": list(set(sources)),
        "found": True,
    }