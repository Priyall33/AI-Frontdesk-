from app.agents.state import AgentState


def fallback_node(state: AgentState) -> AgentState:
    #runs when the router classifies the message as out_of_scope
    
    fallback_message = (
        "I'm here to help with clinic related questions and appointment scheduling. "
        "Could you ask me something about our services, hours, or booking an appointment?"
    )
    
    print(" Fallback agent triggered")
    
    return {
        **state,
        "answer": fallback_message,
        "sources": [],
        "found": False,
    }
