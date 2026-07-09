from dotenv import load_dotenv
load_dotenv()
from langchain_groq import ChatGroq
from app.config import GROQ_API_KEY, GROQ_MODEL
from app.agents.state import AgentState
from app.calendar.google_cal import create_event, check_availability, find_next_available
from datetime import datetime
import json

_llm = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(api_key=GROQ_API_KEY, model_name=GROQ_MODEL, temperature=0.2)
    return _llm

def validate_appointment(date: str, time: str) -> str | None:
    try:
        appt_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return "I couldn't understand that date or time. Please use a format like 'July 10 at 2pm'."
    if appt_dt < datetime.now():
        return "That date has already passed. Please choose a future date."
    if appt_dt.weekday() >= 5:
        return "The clinic is closed on weekends. Please choose a Monday through Friday."
    if not (9 <= appt_dt.hour < 17):
        return "The clinic is open between 9:00 AM and 5:00 PM. Please choose a time within those hours."
    return None

def extract_entities(message: str, entities: dict) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""Extract appointment details from the patient message.
Return a JSON object with these fields (use null if not mentioned):
- patient_name, date (YYYY-MM-DD), time (HH:MM 24hr), reason

Today's date is {today}. Use this to resolve relative dates like "tomorrow" or "next Monday".
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
    entities = extract_entities(message, entities)

    missing = []
    if not entities.get("patient_name"):
        missing.append("your name")
    if not entities.get("date"):
        missing.append("the date you'd like")
    if not entities.get("time"):
        missing.append("your preferred time")

    if not missing:
        validation_error = validate_appointment(entities["date"], entities["time"])
        if validation_error:
            entities.pop("date", None)
            entities.pop("time", None)
            return {**state, "answer": validation_error, "entities": entities, "found": True, "sources": []}

        is_available = check_availability(entities["date"], entities["time"])
        if not is_available:
            next_date, next_time = find_next_available(entities["date"], entities["time"])
            entities.pop("date", None)
            entities.pop("time", None)
            if next_date and next_time:
                next_dt = datetime.strptime(f"{next_date} {next_time}", "%Y-%m-%d %H:%M")
                friendly = next_dt.strftime("%A, %B %d at %I:%M %p")
                answer = (
                    f"Unfortunately that time is already booked. "
                    f"The next available slot is {friendly}. "
                    f"Would you like me to book that for you?"
                )
            else:
                answer = "Unfortunately there are no available slots in the next 7 days. Please call us directly to schedule."
            return {**state, "answer": answer, "entities": entities, "found": True, "sources": []}

        try:
            reason = entities.get("reason", "Clinic Appointment")
            summary = f"{reason} - {entities['patient_name']}"
            create_event(
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
        missing_str = ", ".join(missing)
        answer = f"I'd be happy to book an appointment! Could you please provide: {missing_str}?"

    return {**state, "answer": answer, "entities": entities, "found": True, "sources": []}