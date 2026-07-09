import pytest
from unittest.mock import patch, MagicMock

# Router tests

@patch("app.agents.router.get_llm")
def test_router_faq(mock_get_llm):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="faq")
    mock_get_llm.return_value = mock_llm

    from app.agents.router import router_node
    state = {"message": "What are your hours?", "session_id": "test", "clinic_id": "clinic_001",
             "intent": None, "previous_intent": None, "answer": None,
             "sources": [], "found": False, "chat_history": [], "entities": {}}
    result = router_node(state)
    assert result["intent"] == "faq"

@patch("app.agents.router.get_llm")
def test_router_scheduling(mock_get_llm):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="scheduling")
    mock_get_llm.return_value = mock_llm

    from app.agents.router import router_node
    state = {"message": "I want to book an appointment", "session_id": "test", "clinic_id": "clinic_001",
             "intent": None, "previous_intent": None, "answer": None,
             "sources": [], "found": False, "chat_history": [], "entities": {}}
    result = router_node(state)
    assert result["intent"] == "scheduling"

@patch("app.agents.router.get_llm")
def test_router_invalid_falls_back_to_out_of_scope(mock_get_llm):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="something_random")
    mock_get_llm.return_value = mock_llm

    from app.agents.router import router_node
    state = {"message": "hello", "session_id": "test", "clinic_id": "clinic_001",
             "intent": None, "previous_intent": None, "answer": None,
             "sources": [], "found": False, "chat_history": [], "entities": {}}
    result = router_node(state)
    assert result["intent"] == "out_of_scope"

# FAQ agent tests 

@patch("app.agents.faq_agent.answer_question")
def test_faq_node_found(mock_answer):
    mock_answer.return_value = {"answer": "We open at 9am", "sources": ["faq.csv"], "found": True}

    from app.agents.faq_agent import faq_node
    state = {"message": "What time do you open?", "session_id": "test", "clinic_id": "clinic_001",
             "intent": "faq", "previous_intent": None, "answer": None,
             "sources": [], "found": False, "chat_history": [], "entities": {}}
    result = faq_node(state)
    assert result["found"] is True
    assert "9am" in result["answer"]

@patch("app.agents.faq_agent.answer_question")
def test_faq_node_error_returns_friendly_message(mock_answer):
    mock_answer.side_effect = Exception("Qdrant down")

    from app.agents.faq_agent import faq_node
    state = {"message": "What time do you open?", "session_id": "test", "clinic_id": "clinic_001",
             "intent": "faq", "previous_intent": None, "answer": None,
             "sources": [], "found": False, "chat_history": [], "entities": {}}
    result = faq_node(state)
    assert result["found"] is False
    assert "trouble" in result["answer"].lower() or "call" in result["answer"].lower()

# Scheduling agent tests 
@patch("app.agents.scheduling_agent.check_availability", return_value=True)
@patch("app.agents.scheduling_agent.create_event", return_value={})
@patch("app.agents.scheduling_agent.extract_entities")
def test_scheduling_books_when_all_info_present(mock_extract, mock_create, mock_avail):
    mock_extract.side_effect = lambda msg, entities: entities  # return entities unchanged

    from app.agents.scheduling_agent import scheduling_node
    state = {"message": "book it", "session_id": "test", "clinic_id": "clinic_001",
             "intent": "scheduling", "previous_intent": "scheduling", "answer": None,
             "sources": [], "found": False, "chat_history": [],
             "entities": {"patient_name": "Jane", "date": "2026-12-01", "time": "10:00", "reason": "Checkup"}}
    result = scheduling_node(state)
    assert "booked" in result["answer"].lower()
    mock_create.assert_called_once()

@patch("app.agents.scheduling_agent.extract_entities")
def test_scheduling_asks_for_missing_info(mock_extract):
    mock_extract.side_effect = lambda msg, entities: entities  # no entities extracted

    from app.agents.scheduling_agent import scheduling_node
    state = {"message": "I want an appointment", "session_id": "test", "clinic_id": "clinic_001",
             "intent": "scheduling", "previous_intent": None, "answer": None,
             "sources": [], "found": False, "chat_history": [], "entities": {}}
    result = scheduling_node(state)
    assert "provide" in result["answer"].lower() or "name" in result["answer"].lower()

@patch("app.agents.scheduling_agent.find_next_available", return_value=("2026-12-02", "09:00"))
@patch("app.agents.scheduling_agent.check_availability", return_value=False)
@patch("app.agents.scheduling_agent.extract_entities")
def test_scheduling_suggests_next_slot_when_busy(mock_extract, mock_avail, mock_next):
    mock_extract.side_effect = lambda msg, entities: entities

    from app.agents.scheduling_agent import scheduling_node
    state = {"message": "book it", "session_id": "test", "clinic_id": "clinic_001",
             "intent": "scheduling", "previous_intent": "scheduling", "answer": None,
             "sources": [], "found": False, "chat_history": [],
             "entities": {"patient_name": "Jane", "date": "2026-12-01", "time": "10:00"}}
    result = scheduling_node(state)
    assert "appointment has been booked" not in result["answer"].lower()
    assert "available" in result["answer"].lower()