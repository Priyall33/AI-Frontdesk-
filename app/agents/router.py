from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from app.config import GROQ_API_KEY, GROQ_MODEL
from app.agents.state import AgentState

_llm = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(api_key=GROQ_API_KEY, model_name=GROQ_MODEL, temperature=0)
    return _llm

def router_node(state: AgentState) -> AgentState:
    message = state["message"]
    prompt = f"""You are an intent classifier for a medical clinic assistant.
Classify the patient's message into exactly one of these intents:
- faq: patient is asking a general question about the clinic (hours, location, insurance, services, policies)
- scheduling: patient wants to book, reschedule, or cancel an appointment
- out_of_scope: message is unrelated to the clinic or cannot be handled

Reply with ONLY one word: faq, scheduling, or out_of_scope

Patient message: {message}

Intent:"""
    try:
        response = get_llm().invoke(prompt)
        intent = response.content.strip().lower()
        if intent not in ["faq", "scheduling", "out_of_scope"]:
            intent = "out_of_scope"
    except Exception:
        intent = "out_of_scope"
    return {**state, "intent": intent}