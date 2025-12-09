import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, urlparse
import logging
import html2text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://aide.primlogix.com/prim/fr/5-8/"
visited_urls = set()
pages_content = []

def is_valid_url(url):
    """Check if URL is valid and belongs to the target section."""
    parsed = urlparse(url)
    return url.startswith(BASE_URL) and "aide.primlogix.com" in parsed.netloc

def scrape_page(url):
    """Scrape a single page and extract text."""
    if url in visited_urls:
        return
    visited_urls.add(url)
    
    logger.info(f"Scraping: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract main content - adjusting selector based on common documentation structures
        # If strict selector fails, fallback to body
        content_div = soup.find('main') or soup.find('article') or soup.find('body')
        
        if content_div:
            # Convert HTML to Markdown for better readability for the LLM
            h = html2text.HTML2Text()
            h.ignore_links = False
            text_content = h.handle(str(content_div))
            
            # Extract image URLs from the page
            images = []
            for img in soup.find_all('img', src=True):
                img_src = img.get('src', '')
                if not img_src:
                    continue
                
                # Resolve relative URLs to absolute
                img_url = urljoin(url, img_src)
                
                # Clean URL - remove fragments and query params that might cause issues
                img_url = img_url.split('#')[0]
                
                # Only include images from the same domain or relative paths
                if 'aide.primlogix.com' in img_url or img_src.startswith('/') or img_src.startswith('./'):
                    # Ensure absolute URL
                    if not img_url.startswith('http'):
                        img_url = urljoin(BASE_URL, img_url)
                    
                    # Validate it's a real image URL
                    if any(img_url.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']):
                        images.append({
                            "url": img_url,
                            "alt": img.get('alt', '') or img.get('title', '') or 'Screenshot',
                            "title": img.get('title', '')
                        })
                    # Also include images that might be served dynamically but have image-like paths
                    elif '/images/' in img_url.lower() or '/img/' in img_url.lower() or '/screenshots/' in img_url.lower():
                        images.append({
                            "url": img_url,
                            "alt": img.get('alt', '') or img.get('title', '') or 'Screenshot',
                            "title": img.get('title', '')
                        })
            
            title = soup.title.string if soup.title else url
            pages_content.append({
                "url": url,
                "title": title,
                "content": text_content,
                "images": images  # Store images for this page
            })
            
            # Find all links
            for link in soup.find_all('a', href=True):
                full_url = urljoin(url, link['href'])
                # Remove fragment
                full_url = full_url.split('#')[0]
                
                if is_valid_url(full_url) and full_url not in visited_urls:
                    scrape_page(full_url)
        else:
            logger.warning(f"No content found for {url}")

    except Exception as e:
        logger.error(f"Failed to scrape {url}: {e}")

def run_scraper():
    """Main function to run the scraper."""
    scrape_page(BASE_URL)
    logger.info(f"Scraping complete. Found {len(pages_content)} pages.")
    return pages_content

if __name__ == "__main__":
    data = run_scraper()
    # Save for inspection
    import json
    with open("scraped_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
