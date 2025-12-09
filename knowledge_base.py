import chromadb
from chromadb.utils import embedding_functions
import uuid
import os

# Initialize ChromaDB Client
# PersistentClient ensures data is saved to disk
PERSIST_DIRECTORY = os.path.join(os.getcwd(), "chroma_db")
client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)

# Use a local embedding model (free and fast)
# all-MiniLM-L6-v2 is a good default for sentence-transformers
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Get or create collection
collection = client.get_or_create_collection(
    name="primlogix_docs",
    embedding_function=sentence_transformer_ef
)

def chunk_text(text, chunk_size=1000, overlap=200):
    """Simple text chunking with overlap."""
    if not text:
        return []
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += (chunk_size - overlap)
    return chunks

def add_documents(pages_data):
    """Add a list of page data dicts to the vector DB."""
    ids = []
    documents = []
    metadatas = []

    for page in pages_data:
        url = page['url']
        title = page['title']
        content = page['content']
        images = page.get('images', [])  # Get images for this page
        
        chunks = chunk_text(content)
        
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            
            chunk_id = f"{url}_{i}"
            ids.append(chunk_id)
            documents.append(chunk)
            
            # Store images as JSON string in metadata
            images_json = ""
            if images:
                import json
                images_json = json.dumps(images)
            
            metadatas.append({
                "url": url,
                "title": title,
                "chunk_index": i,
                "images": images_json  # Store images for this chunk
            })

    if documents:
        # Add to collection in batches to avoid hitting limits if any
        batch_size = 100
        total_batches = len(documents) // batch_size + (1 if len(documents) % batch_size > 0 else 0)
        
        for b in range(total_batches):
            start_idx = b * batch_size
            end_idx = start_idx + batch_size
            
            collection.add(
                ids=ids[start_idx:end_idx],
                documents=documents[start_idx:end_idx],
                metadatas=metadatas[start_idx:end_idx]
            )
            print(f"Added batch {b+1}/{total_batches}")
            
    print(f"Total documents in DB: {collection.count()}")

def query_knowledge_base(query, n_results=5):
    """Query the database for relevant chunks."""
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results

if __name__ == "__main__":
    # Test adding some dummy data if run directly but ideally called from a script
    pass
