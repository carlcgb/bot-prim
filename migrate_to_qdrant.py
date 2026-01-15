"""
Migration script to move data from ChromaDB local to Qdrant Cloud.
"""
import os
import sys
from knowledge_base import collection as chroma_collection, chunk_text
from knowledge_base_qdrant import QdrantKnowledgeBase, add_documents
import json

def migrate_chromadb_to_qdrant():
    """Migrate all documents from ChromaDB to Qdrant Cloud."""
    
    # Check Qdrant credentials
    qdrant_url = os.getenv('QDRANT_URL')
    qdrant_api_key = os.getenv('QDRANT_API_KEY')
    
    if not qdrant_url or not qdrant_api_key:
        print("❌ Error: QDRANT_URL and QDRANT_API_KEY environment variables must be set")
        print("\nTo get your credentials:")
        print("1. Go to https://cloud.qdrant.io/")
        print("2. Create a free cluster")
        print("3. Get your cluster URL and API key")
        print("4. Set environment variables:")
        print("   export QDRANT_URL='https://xxx.us-east-1-0.aws.cloud.qdrant.io'")
        print("   export QDRANT_API_KEY='your-api-key'")
        sys.exit(1)
    
    # Check if ChromaDB has data
    try:
        chroma_count = chroma_collection.count()
        print(f"📊 ChromaDB contains {chroma_count} documents")
        
        if chroma_count == 0:
            print("⚠️  ChromaDB is empty. Nothing to migrate.")
            print("   Run 'python ingest.py' first to populate the knowledge base.")
            sys.exit(0)
    except Exception as e:
        print(f"❌ Error accessing ChromaDB: {e}")
        sys.exit(1)
    
    # Initialize Qdrant
    print("\n🔗 Connecting to Qdrant Cloud...")
    try:
        qdrant_client = QdrantKnowledgeBase(url=qdrant_url, api_key=qdrant_api_key)
        print(f"✅ Connected to Qdrant Cloud")
    except Exception as e:
        print(f"❌ Error connecting to Qdrant: {e}")
        sys.exit(1)
    
    # Check existing data in Qdrant
    qdrant_count = qdrant_client.count()
    if qdrant_count > 0:
        response = input(f"\n⚠️  Qdrant already contains {qdrant_count} documents. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            sys.exit(0)
    
    # Fetch all documents from ChromaDB
    print("\n📥 Fetching documents from ChromaDB...")
    try:
        # Get all documents (we'll query with a very broad query to get all)
        # Note: ChromaDB doesn't have a direct "get all" method, so we'll need to query
        # For now, we'll use a workaround: query with empty string and high n_results
        results = chroma_collection.query(
            query_texts=[""],
            n_results=min(chroma_count, 10000),  # Get up to 10k documents
            include=['documents', 'metadatas']
        )
        
        docs = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
        ids = results.get('ids', [[]])[0]
        
        print(f"✅ Retrieved {len(docs)} documents from ChromaDB")
        
        if not docs:
            print("⚠️  No documents found in ChromaDB")
            sys.exit(0)
        
    except Exception as e:
        print(f"❌ Error fetching from ChromaDB: {e}")
        sys.exit(1)
    
    # Reconstruct pages_data format for add_documents
    print("\n🔄 Reconstructing page structure...")
    pages_dict = {}
    
    for doc_id, doc_text, metadata in zip(ids, docs, metadatas):
        url = metadata.get('url', '')
        if not url:
            continue
        
        if url not in pages_dict:
            pages_dict[url] = {
                'url': url,
                'title': metadata.get('title', 'Untitled'),
                'content': '',
                'images': []
            }
        
        # Reconstruct content from chunks
        chunk_index = metadata.get('chunk_index', 0)
        pages_dict[url]['content'] += doc_text + "\n\n"
        
        # Parse images from metadata
        images_json = metadata.get('images', '')
        if images_json:
            try:
                images = json.loads(images_json)
                # Add images if not already present
                existing_urls = {img.get('url', '') for img in pages_dict[url]['images']}
                for img in images:
                    if img.get('url', '') not in existing_urls:
                        pages_dict[url]['images'].append(img)
            except json.JSONDecodeError:
                pass
    
    pages_data = list(pages_dict.values())
    print(f"✅ Reconstructed {len(pages_data)} pages")
    
    # Migrate to Qdrant
    print("\n📤 Migrating to Qdrant Cloud...")
    try:
        add_documents(pages_data, qdrant_client)
        print(f"\n✅ Migration completed successfully!")
        print(f"   ChromaDB: {chroma_count} documents")
        print(f"   Qdrant: {qdrant_client.count()} documents")
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        sys.exit(1)
    
    print("\n🎉 Migration complete!")
    print("\nTo use Qdrant Cloud, set these environment variables:")
    print("  export USE_QDRANT=true")
    print("  export QDRANT_URL='your-url'")
    print("  export QDRANT_API_KEY='your-key'")
    print("\nOr add them to your .env file or Streamlit secrets.")

if __name__ == "__main__":
    migrate_chromadb_to_qdrant()

