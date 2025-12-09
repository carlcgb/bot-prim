from scraper import run_scraper
from knowledge_base import add_documents

if __name__ == "__main__":
    print("Starting ingestion process...")
    
    # 1. Scrape
    print("Scraping documentation...")
    data = run_scraper()
    
    # 2. Add to Vector DB
    print(f"Adding {len(data)} pages to knowledge base...")
    add_documents(data)
    
    print("Ingestion complete!")
