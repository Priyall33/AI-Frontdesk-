from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    """
    Shared state that flows between all agents in the graph.
    Every agent reads from this and writes back to it.
    """
    
    message: str                    # the patient's current message
    session_id: str                 # conversation session ID
    clinic_id: str                  # clinic
    intent: Optional[str]           # what the router decided
    answer: Optional[str]           # final answer to send back to the patient
    sources: Optional[List[str]]    # which FAQ files the answer came from
    found: Optional[bool]           # whether relevant info was found
    chat_history: List[dict]        # full conversation history across turns
    entities: dict                  # collected info like name, date, time, reason