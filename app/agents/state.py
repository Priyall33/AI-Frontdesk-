from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    message: str
    session_id: str
    clinic_id: str
    intent: Optional[str]
    previous_intent: Optional[str]
    answer: Optional[str]
    sources: Optional[List[str]]
    found: Optional[bool]
    chat_history: List[dict]
    entities: dict