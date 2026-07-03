from app.agents.state import AgentState

def fallback_node(state: AgentState) -> AgentState:
    fallback_message = (
        "I'm here to help with clinic-related questions and appointment scheduling. "
        "Could you ask me something about our services, hours, or booking an appointment?"
    )
    print("Fallback agent triggered")
    return {
        **state,
        "answer": fallback_message,
        "sources": [],
        "found": False,
    }
