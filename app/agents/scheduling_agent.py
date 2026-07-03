from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from app.config import GROQ_API_KEY, GROQ_MODEL
from app.agents.state import AgentState
from app.calendar.google_cal import create_event
import json

_llm = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(api_key=GROQ_API_KEY, model_name=GROQ_MODEL, temperature=0.2)
    return _llm


def extract_entities(message: str, entities: dict) -> dict:
    #pull appointment details out of the patient's message
    prompt = f"""Extract appointment details from the patient message.
Return a JSON object with these fields (use null if not mentioned):
- patient_name: the patient's name
- date: appointment date (convert to YYYY-MM-DD format if possible, today is 2026-07-03)
- time: appointment time in HH:MM 24hr format
- reason: reason for visit

Already collected info: {json.dumps(entities)}
Patient message: {message}

Return ONLY valid JSON, nothing else:"""

    response = get_llm().invoke(prompt)
    
    try:
        extracted = json.loads(response.content.strip())
        for key, value in extracted.items():
            if value is not None:
                entities[key] = value
    except json.JSONDecodeError:
        pass 
    
    return entities


def scheduling_node(state: AgentState) -> AgentState:
    message = state["message"]
    entities = state.get("entities", {})
    
    #extract appointment details from the message
    entities = extract_entities(message, entities)
    
    missing = []
    if not entities.get("patient_name"):
        missing.append("your name")
    if not entities.get("date"):
        missing.append("the date you'd like")
    if not entities.get("time"):
        missing.append("your preferred time")
 
    if not missing:
        try:
            reason = entities.get("reason", "Clinic Appointment")
            summary = f"{reason} - {entities['patient_name']}"
            
            event = create_event(
                summary=summary,
                date=entities["date"],
                time=entities["time"],
                duration_hours=1,
                description=f"Patient: {entities['patient_name']}\nReason: {reason}",
            )
            
            answer = (
                f"Your appointment has been booked! Here are the details:\n"
                f"- Name: {entities['patient_name']}\n"
                f"- Date: {entities['date']}\n"
                f"- Time: {entities['time']}\n"
                f"- Reason: {reason}\n"
                f"You'll see it on your calendar. Is there anything else I can help you with?"
            )
            
            entities = {}
            
        except Exception as e:
            answer = f"I had trouble booking the appointment: {str(e)}. Please try again or call us directly."
    
    else:
        #missing info
        missing_str = ", ".join(missing)
        answer = f"I'd be happy to book an appointment! Could you please provide: {missing_str}?"
    
    return {
        **state,
        "answer": answer,
        "entities": entities,
        "found": True,
        "sources": [],
    }