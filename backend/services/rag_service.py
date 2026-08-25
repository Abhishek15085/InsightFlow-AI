import os
import pandas as pd
import chromadb
import re

# Create a local persistent Chroma client in the project root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CHROMA_DB_DIR = os.path.join(ROOT_DIR, "chroma_db")
os.makedirs(CHROMA_DB_DIR, exist_ok=True)

chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

def get_collection_name(filename: str) -> str:
    """Clean filename to be a valid Chroma collection name."""
    name = re.sub(r'[^a-zA-Z0-9]', '_', filename)
    name = name.strip('_')
    if len(name) < 3:
        name = name + "_col"
    return name[:63]

def index_dataset(filename: str, df: pd.DataFrame):
    """Embed and index dataset rows into ChromaDB"""
    collection_name = get_collection_name(filename)
    
    # We use get_or_create_collection so it doesn't fail if it exists.
    # Note: If it exists, we might want to skip or clear it if it's an overwrite, 
    # but for now we'll just delete and recreate to ensure it's fresh.
    try:
        chroma_client.delete_collection(name=collection_name)
    except Exception:
        pass
        
    collection = chroma_client.create_collection(name=collection_name)
    
    # Process dataframe into text docs
    # Index up to 5000 rows to prevent long blocking uploads
    max_rows = 5000
    df_subset = df.head(max_rows)
    
    documents = []
    metadatas = []
    ids = []
    
    for idx, row in df_subset.iterrows():
        # Convert row to a readable string: "Col1: Val1, Col2: Val2"
        doc_str = ", ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
        documents.append(doc_str)
        metadatas.append({"row_index": idx})
        ids.append(f"row_{idx}")
        
    # Add to chroma in batches
    batch_size = 1000
    for i in range(0, len(documents), batch_size):
        collection.add(
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
            ids=ids[i:i+batch_size]
        )
        
def query_dataset(filename: str, query: str, top_k: int = 50) -> str:
    """Query ChromaDB for relevant rows based on natural language."""
    collection_name = get_collection_name(filename)
    try:
        collection = chroma_client.get_collection(name=collection_name)
    except Exception:
        return "" # Collection doesn't exist yet
        
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )
    
    if not results['documents'] or not results['documents'][0]:
        return ""
        
    retrieved_docs = results['documents'][0]
    
    context = "Here are the most relevant retrieved rows from the dataset based on the user's query:\n"
    for i, doc in enumerate(retrieved_docs):
        context += f"Row {i+1}: {doc}\n"
        
    return context
