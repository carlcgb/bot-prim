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
            
            # Extract image URLs from the page with enhanced context
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
                    # Ensure absolute URL - always convert to full URL
                    if not img_url.startswith('http'):
                        # If still relative, use the page URL as base
                        img_url = urljoin(url, img_src)
                        if not img_url.startswith('http'):
                            # Final fallback to BASE_URL
                            img_url = urljoin(BASE_URL, img_src)
                    
                    # Final check - ensure it's absolute
                    if not img_url.startswith('http'):
                        continue  # Skip if we can't make it absolute
                    
                    # Extract context around the image for better understanding
                    # Get parent element and nearby text
                    parent = img.find_parent(['div', 'section', 'article', 'figure', 'p'])
                    context_text = ""
                    if parent:
                        # Get text before and after the image
                        parent_text = parent.get_text(separator=' ', strip=True)
                        # Limit context to 200 chars
                        context_text = parent_text[:200] if parent_text else ""
                    
                    # Get figure caption if exists
                    figure_caption = ""
                    figure = img.find_parent('figure')
                    if figure:
                        figcaption = figure.find('figcaption')
                        if figcaption:
                            figure_caption = figcaption.get_text(strip=True)
                    
                    # FILTER OUT ICONS AND SMALL LOGOS - Only keep real screenshots
                    # Check image dimensions from HTML attributes
                    img_width = img.get('width', '')
                    img_height = img.get('height', '')
                    
                    # Convert to integers if they're numeric strings
                    width_val = None
                    height_val = None
                    try:
                        if img_width and str(img_width).isdigit():
                            width_val = int(img_width)
                        if img_height and str(img_height).isdigit():
                            height_val = int(img_height)
                    except (ValueError, AttributeError):
                        pass
                    
                    # Filter criteria: exclude small icons/logos
                    # Icons are typically < 100px in either dimension
                    is_small_icon = False
                    if width_val and width_val < 100:
                        is_small_icon = True
                    if height_val and height_val < 100:
                        is_small_icon = True
                    
                    # Filter by filename - exclude common icon/logo patterns
                    img_filename = img_url.lower()
                    icon_patterns = [
                        'icon', 'logo', 'button', 'arrow', 'chevron', 
                        'nav', 'menu', 'bullet', 'dot', 'star', 'check',
                        'close', 'delete', 'edit', 'add', 'remove',
                        '40x40', '32x32', '24x24', '16x16', '20x20',
                        'favicon', 'sprite', 'glyph'
                    ]
                    
                    # Check if filename suggests it's an icon/logo
                    is_icon_filename = any(pattern in img_filename for pattern in icon_patterns)
                    
                    # Filter by alt/title text - exclude generic icon descriptions
                    alt_text = img.get('alt', '') or img.get('title', '') or ''
                    title_text = img.get('title', '')
                    combined_text = (alt_text + ' ' + title_text).lower()
                    icon_text_patterns = ['icon', 'logo', 'button', 'arrow', 'chevron', 'nav']
                    is_icon_text = any(pattern in combined_text for pattern in icon_text_patterns)
                    
                    # Skip if it's clearly an icon/logo
                    if is_small_icon or (is_icon_filename and not any(x in img_filename for x in ['screenshot', 'capture', 'interface', 'fenetre', 'ecran'])):
                        continue
                    if is_icon_text and not any(x in combined_text for x in ['screenshot', 'capture', 'interface', 'fenetre', 'ecran', 'affichage']):
                        continue
                    
                    # Only include images that look like screenshots:
                    # - Have reasonable size (or no size specified, which usually means full-size)
                    # - Are in /images/ directory (where screenshots are typically stored)
                    # - Have screenshot-related keywords in filename or context
                    is_likely_screenshot = False
                    if '/images/' in img_url.lower():
                        is_likely_screenshot = True
                    if any(keyword in img_filename for keyword in ['screenshot', 'capture', 'interface', 'fenetre', 'ecran', 'affichage', 'window', 'dialog']):
                        is_likely_screenshot = True
                    if any(keyword in context_text.lower() for keyword in ['capture', 'screenshot', 'interface', 'fenetre', 'ecran', 'affichage']):
                        is_likely_screenshot = True
                    if figure_caption and any(keyword in figure_caption.lower() for keyword in ['capture', 'screenshot', 'interface', 'fenetre', 'ecran']):
                        is_likely_screenshot = True
                    
                    # Skip if it doesn't look like a screenshot
                    if not is_likely_screenshot:
                        continue
                    
                    # Build enhanced description
                    description_parts = []
                    if alt_text:
                        description_parts.append(alt_text)
                    if title_text and title_text != alt_text:
                        description_parts.append(title_text)
                    if figure_caption:
                        description_parts.append(f"Légende: {figure_caption}")
                    if context_text:
                        # Add context as description
                        description_parts.append(f"Contexte: {context_text}")
                    
                    enhanced_description = " | ".join(description_parts) if description_parts else 'Capture d\'écran de l\'interface PrimLogix'
                    
                    # Only include real image files (exclude SVG which are often icons)
                    if any(img_url.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                        images.append({
                            "url": img_url,
                            "alt": alt_text or 'Screenshot',
                            "title": title_text or '',
                            "description": enhanced_description,  # Enhanced description with context
                            "context": context_text,  # Context around the image
                            "caption": figure_caption,  # Figure caption if available
                            "width": width_val,  # Store dimensions for later filtering
                            "height": height_val
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
