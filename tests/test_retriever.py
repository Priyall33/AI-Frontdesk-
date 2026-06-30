# tests/test_retriever.py

from app.rag.retriever import answer_question

def test_answer_question():
    result = answer_question("What are your clinic hours?")
    print(f"\nAnswer: {result['answer']}")
    print(f"Sources: {result['sources']}")
    assert result["found"] == True
    assert len(result["answer"]) > 0

def test_no_answer():
    result = answer_question("What is the meaning of life?")
    print(f"\nFallback: {result['answer']}")
    assert result["found"] == False