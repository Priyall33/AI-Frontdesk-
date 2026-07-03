from app.agents.state import AgentState
from app.rag.retriever import answer_question

def faq_node(state: AgentState) -> AgentState:
    message = state["message"]
    clinic_id = state["clinic_id"]
    result = answer_question(query=message, clinic_id=clinic_id)
    print(f"FAQ agent answered. Found: {result['found']}")
    return {
        **state,
        "answer": result["answer"],
        "sources": result["sources"],
        "found": result["found"],
    }
