_sessions: dict = {}

def get_history(session_id: str) -> list:
    return _sessions.get(session_id, [])

def update_history(session_id: str, role: str, content: str):
    if session_id not in _sessions:
        _sessions[session_id] = []
    _sessions[session_id].append({"role": role, "content": content})

def get_entities(session_id: str) -> dict:
    return _sessions.get(f"{session_id}_entities", {})

def update_entities(session_id: str, entities: dict):
    _sessions[f"{session_id}_entities"] = entities

def get_session_intent(session_id: str) -> str:
    # remembers the last intent 
    return _sessions.get(f"{session_id}_intent", "")

def update_session_intent(session_id: str, intent: str):
    _sessions[f"{session_id}_intent"] = intent

def clear_session(session_id: str):
    _sessions.pop(session_id, None)
    _sessions.pop(f"{session_id}_entities", None)
    _sessions.pop(f"{session_id}_intent", None)