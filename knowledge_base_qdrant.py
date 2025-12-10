"""
Qdrant Cloud integration for knowledge base storage.
Provides the same interface as ChromaDB for seamless migration.
"""
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import json
import logging
import uuid

logger = logging.getLogger(__name__)

# Initialize embedding model (same as ChromaDB for consistency)
EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
EMBEDDING_DIM = 384  # Dimension for all-MiniLM-L6-v2

class QdrantKnowledgeBase:
    """Qdrant Cloud knowledge base wrapper with ChromaDB-compatible interface."""
    
    def __init__(self, url=None, api_key=None, collection_name="primlogix_docs"):
        """
        Initialize Qdrant client.
        
        Args:
            url: Qdrant Cloud cluster URL (e.g., https://xxx.us-east-1-0.aws.cloud.qdrant.io)
            api_key: Qdrant Cloud API key
            collection_name: Name of the collection
        """
        # Get credentials from environment or parameters
        self.url = url or os.getenv('QDRANT_URL')
        self.api_key = api_key or os.getenv('QDRANT_API_KEY')
        self.collection_name = collection_name
        
        if not self.url or not self.api_key:
            raise ValueError(
                "Qdrant credentials not found. Please set QDRANT_URL and QDRANT_API_KEY environment variables, "
                "or provide them as parameters. Get them from: https://cloud.qdrant.io/"
            )
        
        # Initialize Qdrant client
        self.client = QdrantClient(
            url=self.url,
            api_key=self.api_key,
        )
        
        # Initialize collection if it doesn't exist
        self._ensure_collection()
        
        logger.info(f"Connected to Qdrant Cloud: {self.url}")
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=EMBEDDING_DIM,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection '{self.collection_name}' created successfully")
            else:
                logger.info(f"Collection '{self.collection_name}' already exists")
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise
    
    def _embed_text(self, text):
        """Generate embedding for text."""
        return EMBEDDING_MODEL.encode(text).tolist()
    
    def count(self):
        """Get total number of documents in collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return info.points_count
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            return 0
    
    def _generate_point_id(self, original_id):
        """
        Generate a valid Qdrant point ID from an original ID.
        Qdrant accepts only unsigned integers or UUIDs.
        We'll use a hash-based approach to generate consistent UUIDs.
        """
        # Create a deterministic UUID from the original ID
        # This ensures the same document always gets the same ID
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
        return str(uuid.uuid5(namespace, str(original_id)))
    
    def add(self, ids, documents, metadatas):
        """
        Add documents to Qdrant.
        
        Args:
            ids: List of document IDs (will be converted to UUIDs)
            documents: List of document texts
            metadatas: List of metadata dicts
        """
        if not ids or not documents:
            return
        
        points = []
        for i, (doc_id, doc_text, metadata) in enumerate(zip(ids, documents, metadatas)):
            # Generate embedding
            embedding = self._embed_text(doc_text)
            
            # Convert ID to valid Qdrant format (UUID)
            qdrant_id = self._generate_point_id(doc_id)
            
            # Store original ID in metadata for reference
            metadata_with_original_id = {
                **metadata,
                "original_id": doc_id,  # Keep original ID for reference
                "text": doc_text  # Store text in payload for retrieval
            }
            
            # Prepare point
            point = PointStruct(
                id=qdrant_id,
                vector=embedding,
                payload=metadata_with_original_id
            )
            points.append(point)
        
        # Upsert points in batches
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Added {len(points)} documents to Qdrant")
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def query(self, query_texts, n_results=10, include=None):
        """
        Query Qdrant for similar documents.
        
        Args:
            query_texts: List of query strings (only first one is used)
            n_results: Number of results to return
            include: List of fields to include (for compatibility with ChromaDB)
        
        Returns:
            Dictionary with 'documents', 'metadatas', 'distances', 'ids' (ChromaDB-compatible format)
        """
        if not query_texts:
            return {
                'documents': [[]],
                'metadatas': [[]],
                'distances': [[]],
                'ids': [[]]
            }
        
        query_text = query_texts[0]
        query_embedding = self._embed_text(query_text)
        
        try:
            # Search in Qdrant using query_points (correct API method)
            # Use NamedSparseVector or just pass vector directly
            search_results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,  # Pass vector directly
                limit=n_results,
                with_payload=True
            )
            
            # Convert to ChromaDB-compatible format
            documents = []
            metadatas = []
            distances = []
            ids = []
            
            # Extract points from QueryResult object
            points = search_results.points if hasattr(search_results, 'points') else []
            
            for result in points:
                # Use original_id if available, otherwise use Qdrant ID
                payload = result.payload if hasattr(result, 'payload') else {}
                if not payload:
                    payload = {}
                
                point_id = result.id if hasattr(result, 'id') else ''
                original_id = payload.get('original_id', point_id) if isinstance(payload, dict) else point_id
                ids.append(original_id)
                
                # Extract text from payload
                text = payload.pop('text', '') if isinstance(payload, dict) else ''
                documents.append(text)
                
                # Remove original_id from metadata (it's not part of the original metadata)
                if isinstance(payload, dict):
                    payload.pop('original_id', None)
                
                # Metadata is the rest of the payload
                metadatas.append(payload)
                
                # Convert distance to similarity score (1 - distance for cosine)
                score = result.score if hasattr(result, 'score') else 0
                distance = 1 - score if score <= 1 else score
                distances.append(distance)
            
            return {
                'documents': [documents],
                'metadatas': [metadatas],
                'distances': [distances],
                'ids': [ids]
            }
        except Exception as e:
            logger.error(f"Error querying Qdrant: {e}")
            return {
                'documents': [[]],
                'metadatas': [[]],
                'distances': [[]],
                'ids': [[]]
            }


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


def add_documents(pages_data, qdrant_client):
    """Add a list of page data dicts to Qdrant."""
    ids = []
    documents = []
    metadatas = []

    for page in pages_data:
        url = page['url']
        title = page['title']
        content = page['content']
        images = page.get('images', [])
        
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
                images_json = json.dumps(images)
            
            metadatas.append({
                "url": url,
                "title": title,
                "chunk_index": i,
                "images": images_json
            })

    if documents:
        # Add to Qdrant in batches
        batch_size = 100
        total_batches = len(documents) // batch_size + (1 if len(documents) % batch_size > 0 else 0)
        
        for b in range(total_batches):
            start_idx = b * batch_size
            end_idx = start_idx + batch_size
            
            qdrant_client.add(
                ids=ids[start_idx:end_idx],
                documents=documents[start_idx:end_idx],
                metadatas=metadatas[start_idx:end_idx]
            )
            print(f"Added batch {b+1}/{total_batches} to Qdrant")
    
    print(f"Total documents in Qdrant: {qdrant_client.count()}")


def query_knowledge_base(query, n_results=10, qdrant_client=None):
    """
    Query Qdrant for relevant chunks.
    
    Args:
        query: Search query string
        n_results: Number of results to return
        qdrant_client: QdrantKnowledgeBase instance
    
    Returns:
        Dictionary with 'documents', 'metadatas', 'distances', and 'ids'
    """
    if not qdrant_client:
        raise ValueError("Qdrant client not provided")
    
    return qdrant_client.query(
        query_texts=[query],
        n_results=n_results,
        include=['documents', 'metadatas', 'distances']
    )

