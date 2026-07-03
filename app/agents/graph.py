from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.router import router_node
from app.agents.faq_agent import faq_node
from app.agents.fallback_agent import fallback_node

def route_intent(state: AgentState) -> str:
    intent = state.get("intent", "out_of_scope")
    if intent == "faq":
        return "faq"
    elif intent == "scheduling":
        return "fallback"
    else:
        return "fallback"

graph_builder = StateGraph(AgentState)
graph_builder.add_node("router", router_node)
graph_builder.add_node("faq", faq_node)
graph_builder.add_node("fallback", fallback_node)
graph_builder.set_entry_point("router")
graph_builder.add_conditional_edges("router", route_intent, {"faq": "faq", "fallback": "fallback"})
graph_builder.add_edge("faq", END)
graph_builder.add_edge("fallback", END)
graph = graph_builder.compile()

def run_agent(message: str, session_id: str = "default", clinic_id: str = "clinic_001") -> dict:
    initial_state: AgentState = {
        "message": message,
        "session_id": session_id,
        "clinic_id": clinic_id,
        "intent": None,
        "answer": None,
        "sources": [],
        "found": False,
        "chat_history": [],
        "entities": {},
    }
    final_state = graph.invoke(initial_state)
    return {
        "answer": final_state["answer"],
        "intent": final_state["intent"],
        "sources": final_state["sources"],
        "found": final_state["found"],
        "session_id": session_id,
    }
