import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def _load_env_file():
    """Load .env values if present and env vars are not already set."""
    env_path = Path('.env')
    if not env_path.exists():
        return
    try:
        with env_path.open('r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception as e:
        logger.warning(f"Could not load .env file: {e}")


_load_env_file()

# Determine which backend to use (Qdrant Cloud or ChromaDB local)
USE_QDRANT = os.getenv('USE_QDRANT', 'false').lower() == 'true'
QDRANT_URL = os.getenv('QDRANT_URL')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')

# Global variables for backend
collection = None
qdrant_client = None

# Initialize backend
if USE_QDRANT and QDRANT_URL and QDRANT_API_KEY:
    # Use Qdrant Cloud
    try:
        logger.info(f"Using Qdrant Cloud for knowledge base: {QDRANT_URL[:50] if QDRANT_URL else 'N/A'}...")
        try:
            from knowledge_base_qdrant import QdrantKnowledgeBase
        except (ImportError, KeyError, AttributeError, Exception) as import_error:
            logger.warning(f"Could not import QdrantKnowledgeBase: {import_error}")
            # Don't raise - fall through to ChromaDB fallback
            USE_QDRANT = False
            qdrant_client = None
        else:
            # Only initialize if import succeeded
            qdrant_client = QdrantKnowledgeBase(url=QDRANT_URL, api_key=QDRANT_API_KEY)
            collection = qdrant_client  # Compatible interface
            logger.info("✅ Qdrant Cloud initialized successfully")
    except (KeyError, ImportError, AttributeError, Exception) as e:
        logger.warning(f"Failed to initialize Qdrant: {e}")
        import traceback
        logger.warning(traceback.format_exc())
        logger.info("Falling back to ChromaDB local")
        USE_QDRANT = False
        qdrant_client = None

if not USE_QDRANT or not qdrant_client:
    # Use ChromaDB local (default)
    logger.info("Using ChromaDB local for knowledge base")
    import chromadb
    from chromadb.utils import embedding_functions
    
    PERSIST_DIRECTORY = os.path.join(os.getcwd(), "chroma_db")
    client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
    
    # Use a local embedding model (free and fast)
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    # Get or create collection
    collection = client.get_or_create_collection(
        name="primlogix_docs",
        embedding_function=sentence_transformer_ef
    )


def chunk_text(text, chunk_size=800, overlap=150):
    """
    Optimized text chunking with overlap.
    Reduced chunk size from 1000 to 800 for better relevance and faster processing.
    Reduced overlap from 200 to 150 for less redundancy.
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        # Only add non-empty chunks
        if chunk.strip():
            chunks.append(chunk)
        start += (chunk_size - overlap)
    return chunks


def add_documents(pages_data):
    """Add a list of page data dicts to the vector DB."""
    if USE_QDRANT and qdrant_client:
        # Use Qdrant
        from knowledge_base_qdrant import add_documents as qdrant_add
        qdrant_add(pages_data, qdrant_client)
        return
    
    # Use ChromaDB
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


def query_knowledge_base(query, n_results=10):
    """Query the database for relevant chunks.
    
    Args:
        query: Search query string
        n_results: Number of results to return (default: 10 for better context)
    
    Returns:
        Dictionary with 'documents', 'metadatas', 'distances', and 'ids'
    """
    if USE_QDRANT and qdrant_client:
        # Use Qdrant
        from knowledge_base_qdrant import query_knowledge_base as qdrant_query
        return qdrant_query(query, n_results, qdrant_client)
    else:
        # Use ChromaDB
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        return results


if __name__ == "__main__":
    # Test adding some dummy data if run directly but ideally called from a script
    pass
