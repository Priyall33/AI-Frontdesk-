from app.agents.state import AgentState
from app.rag.retriever import answer_question

def faq_node(state: AgentState) -> AgentState:
    try: 
        result = answer_question(query=state["message"], clinic_id=state["clinic_id"])
        return {
            **state,
            "answer": result["answer"],
            "sources": result["sources"],
            "found": result["found"],
        }
    except Exception:
        return {
            **state,
            "answer": "I don't have that information available. Would you like me to have someone from the clinic call you back?",
            "sources": [],
            "found": False,
        }