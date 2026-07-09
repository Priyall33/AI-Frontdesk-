from langchain_community.document_loaders import (
    PyPDFLoader, #reads pdf files
    Docx2txtLoader, #reads word docs 
    TextLoader, 
    CSVLoader, #reads spreadsheets 
)
from langchain_text_splitters import RecursiveCharacterTextSplitter  # tool splits into chunks 
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient #connects to qdrant database 
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain_core.documents import Document
from app.config import (
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_COLLECTION,
    EMBEDDING_MODEL,
    CLINIC_ID,
)
import pandas as pd
import uuid #unique id for each chunk 
import os


embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

# Connect to Qdrant
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

def create_collection_if_not_exists():
  
    existing = [c.name for c in client.get_collections().collections] #creates a qdrant collections if they dont exist where FAQ chucks will be stored 
    
    if QDRANT_COLLECTION not in existing:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=384,        
                distance=Distance.COSINE,  # measure similarity by angle between vectors
            ),
        )
        print(f"Created collection: {QDRANT_COLLECTION}")
    else:
        print(f"Collection already exists: {QDRANT_COLLECTION}")

def load_and_split(file_path: str):
    
    ext = os.path.splitext(file_path)[1].lower() 
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,   # each chunk max 500 characters
        chunk_overlap=50,
    )

    # pick the right loader based on file type
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".docx":
        loader = Docx2txtLoader(file_path)
    elif ext == ".txt":
        loader = TextLoader(file_path)
    elif ext == ".csv":
        loader = CSVLoader(file_path, encoding="latin-1")
    elif ext == ".xlsx":
        # read excel, convert each row to a text document
        df = pd.read_excel(file_path)
        documents = []
        for _, row in df.iterrows():
            text = " | ".join(f"{col}: {val}" for col, val in row.items() if pd.notna(val))
            documents.append(Document(page_content=text, metadata={"source": file_path}))
        return splitter.split_documents(documents)
    else:
        raise ValueError(f"Unsupported file type: {ext}") # crash with clear message if unsupported
    
    documents = loader.load() # read file and extract all text

    return splitter.split_documents(documents) # returns list of chunks

def ingest_file(file_path: str, clinic_id: str = CLINIC_ID):
    
    create_collection_if_not_exists() 
    
    chunks = load_and_split(file_path) 
    
    points = [] 
    
    for chunk in chunks:
        embedding = embeddings.embed_query(chunk.page_content) 
        
        point = PointStruct(
            id=str(uuid.uuid4()),       
            vector=embedding,           
            payload={
                "text": chunk.page_content,      
                "clinic_id": clinic_id,           
                "source": os.path.basename(file_path), 
            }
        )
        points.append(point)
    
    # upload all chunks to qdrant in one batch
    client.upsert(
        collection_name=QDRANT_COLLECTION,
        points=points,
    )
    
    print(f" Ingested {len(points)} chunks from {os.path.basename(file_path)}")
    return len(points)