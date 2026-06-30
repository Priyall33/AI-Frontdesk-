
import os
from app.rag.ingestor import ingest_file

def test_ingest():
    # build absolute path so it works regardless of where pytest is run from
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_data", "clinic_faq.txt")
    count = ingest_file(file_path)
    print(f" Stored {count} chunks in Qdrant")
    assert count > 0, "No chunks were stored — something went wrong"