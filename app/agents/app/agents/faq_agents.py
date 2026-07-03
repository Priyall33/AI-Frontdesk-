from app.agents.state import AgentState
from app.rag.retriever import answer_question


def faq_node(state: AgentState) -> AgentState:
    #patient's message from shared state 
    message = state["message"]
    clinic_id = state["clinic_id"]
    
    # call the RAG retriever 
    result = answer_question(query=message, clinic_id=clinic_id)
    
    print(f"FAQ agent answered. Found: {result['found']}")
    
    #ans back to stared state 
    return {
        **state,
        "answer": result["answer"],
        "sources": result["sources"],
        "found": result["found"],
    }