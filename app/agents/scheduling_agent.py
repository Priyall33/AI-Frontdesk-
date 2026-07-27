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
        _llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name=GROQ_MODEL,
            temperature=0,
            model_kwargs={"response_format": {"type": "json_object"}}
        )
    return _llm

def validate_appointment(date: str, time: str) -> str | None:
    try:
        appt_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return "I'm sorry, I didn't quite catch that date and time! Could you try again in a format like 'July 15 at 2pm'? I want to make sure we get you booked correctly."
    if appt_dt < datetime.now():
        return "Oh it looks like that date has already passed! Could you pick a future date? I want to make sure we get you in at the right time."
    if appt_dt.weekday() >= 5:
        return "I'm sorry, our clinic is closed on weekends! We're open Monday through Friday. Would any of those days work for you?"
    if not (9 <= appt_dt.hour < 17):
        return "Our clinic hours are 9:00 AM to 5:00 PM Monday through Friday. Could you pick a time within those hours? I want to make sure someone is here to take care of you!"
    return None

def extract_entities(message: str, entities: dict) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""Extract appointment details from this patient message.
Today is {today}. Convert relative dates like "tomorrow" or "next Monday" to YYYY-MM-DD format.
Convert times like "3pm" to "15:00", "9am" to "09:00", "morning" to "09:00", "afternoon" to "14:00".

IMPORTANT: Only extract information EXPLICITLY stated in the message. If no date is mentioned, date must be null. If no time is mentioned, time must be null. Do NOT assume or guess any values.

Already collected: {json.dumps(entities)}
Patient message: {message}

Return ONLY valid JSON with these exact keys (use null if not explicitly in message):
{{"patient_name": null, "date": null, "time": null, "reason": null}}"""
    response = get_llm().invoke(prompt)
    print("EXTRACTED RAW:", response.content)
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
        missing.append("your full name")
    if not entities.get("date"):
        missing.append("the date you'd like to come in")
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
                    f"Oh I'm so sorry, it looks like that time slot is already taken! "
                    f"The next available opening I have is {friendly}. "
                    f"Would that work for you? I'd love to get you booked in!"
                )
            else:
                answer = "I'm so sorry, it looks like we're completely booked for the next 7 days! I'd recommend giving us a call directly so we can find a solution for you as soon as possible."
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
                f"Perfect, you are all set {entities['patient_name']}! I've gone ahead and booked your appointment. Here's a summary of your visit:\n\n"
                f"- Name: {entities['patient_name']}\n"
                f"- Date: {entities['date']}\n"
                f"- Time: {entities['time']}\n"
                f"- Reason: {reason}\n\n"
                f"Please arrive about 10 minutes early to complete any paperwork, and don't forget to bring your insurance card and a valid photo ID. "
                f"If you need to reschedule or have any questions before your visit, don't hesitate to reach out. We look forward to seeing you!"
            )
            entities = {"patient_name": entities.get("patient_name", "")}
        except Exception as e:
            answer = "I'm so sorry, I ran into a little issue trying to book that for you! Could you try again in a moment, or feel free to give us a call directly and we'll get you taken care of right away."
    else:
        if len(missing) == 3:
            answer = "Of course, I'd be happy to help get you scheduled! To book your appointment I'll just need a few details — could you start by sharing your full name?"
        else:
            missing_str = ", ".join(missing)
            answer = f"Almost there! I just need a little more information to complete your booking — could you share {missing_str}?"

    return {**state, "answer": answer, "entities": entities, "found": True, "sources": []}