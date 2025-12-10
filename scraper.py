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
        # Ensure proper encoding
        response.encoding = response.apparent_encoding or 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract main content - adjusting selector based on common documentation structures
        # If strict selector fails, fallback to body
        content_div = soup.find('main') or soup.find('article') or soup.find('body')
        
        if content_div:
            # Convert HTML to Markdown for better readability for the LLM
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.unicode_snob = True  # Preserve Unicode characters
            text_content = h.handle(str(content_div))
            # Ensure UTF-8 encoding
            if isinstance(text_content, bytes):
                text_content = text_content.decode('utf-8', errors='ignore')
            
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
                    
                    # Filter criteria: exclude small icons/logos and square icon formats
                    # Icons are typically < 100px in either dimension
                    # Also exclude square formats like 63x63, 64x64, etc. (common icon sizes)
                    is_small_icon = False
                    is_square_icon = False
                    
                    if width_val and width_val < 100:
                        is_small_icon = True
                    if height_val and height_val < 100:
                        is_small_icon = True
                    
                    # Exclude square icon formats (63x63, 64x64, 48x48, 32x32, etc.)
                    # Icons are often perfect squares and small
                    if width_val and height_val:
                        # Check if it's a square (width == height) and small (common icon sizes)
                        if width_val == height_val:
                            # Common icon square sizes to exclude
                            common_icon_sizes = [16, 20, 24, 32, 40, 48, 50, 56, 60, 63, 64, 72, 80, 96, 100, 128]
                            if width_val in common_icon_sizes:
                                is_square_icon = True
                            # Also exclude any square smaller than 150px (likely an icon)
                            elif width_val < 150:
                                is_square_icon = True
                    
                    # Filter by filename - exclude common icon/logo/arrow/emoji patterns
                    img_filename = img_url.lower()
                    icon_patterns = [
                        'icon', 'logo', 'button', 'arrow', 'chevron', 'fleche', 'flèche',
                        'nav', 'menu', 'bullet', 'dot', 'star', 'check', 'emoji',
                        'close', 'delete', 'edit', 'add', 'remove', 'plus', 'minus',
                        '40x40', '32x32', '24x24', '16x16', '20x20', '30x30', '48x48',
                        '50x50', '56x56', '60x60', '63x63', '64x64', '72x72', '80x80',
                        '96x96', '100x100', '128x128',
                        'favicon', 'sprite', 'glyph', 'svg', 'ico',
                        'up', 'down', 'left', 'right', 'next', 'prev', 'previous',
                        'haut', 'bas', 'gauche', 'droite', 'suivant', 'precedent',
                        # Specific icon types
                        'lightbulb', 'ampoule', 'bulb', 'lamp', 'lampe',
                        'placeholder', 'place-holder', 'generic', 'generique',
                        # Person/people icons
                        'person', 'people', 'user', 'utilisateur', 'profil', 'profile',
                        'head', 'shoulder', 'silhouette', 'avatar', 'tête', 'épaules',
                        # Checkmark/verification icons
                        'checkmark', 'check', 'verification', 'vérification', 'tick', 'coche',
                        'check-icon', 'icone-check', 'icone-verification',
                        # Remuneration/payment icons
                        'remuneration', 'rémunération', 'payment', 'paiement', 'money', 'argent',
                        'cash', 'hand-money', 'main-argent', 'salary', 'salaire',
                        # Feedback icons (thumbs up/down)
                        'thumbs', 'thumbs-up', 'thumbs-down', 'thumbsup', 'thumbsdown',
                        'thumb-up', 'thumb-down', 'like', 'dislike', 'feedback',
                        'pouce', 'pouce-haut', 'pouce-bas',
                        # Document/folder icons (NOT screenshots)
                        'document', 'doc', 'file', 'folder', 'dossier', 'cv', 'resume',
                        'pdf-icon', 'word-icon', 'excel-icon', 'file-icon', 'folder-icon',
                        'document-icon', 'icone-document', 'icone-dossier', 'icone-fichier',
                        # Warning/stop sign icons
                        'stop', 'stop-sign', 'stop-signal', 'arret', 'arrêt', 'warning',
                        'avertissement', 'alert', 'alerte', 'danger', 'attention',
                        'octagon', 'octogone', 'stop-icon', 'icone-arret', 'icone-stop'
                    ]
                    
                    # Check if filename suggests it's an icon/logo/arrow/emoji
                    is_icon_filename = any(pattern in img_filename for pattern in icon_patterns)
                    
                    # Filter by alt/title text - exclude generic icon/arrow/emoji descriptions
                    alt_text = img.get('alt', '') or img.get('title', '') or ''
                    title_text = img.get('title', '')
                    combined_text = (alt_text + ' ' + title_text).lower()
                    icon_text_patterns = [
                        'icon', 'logo', 'button', 'arrow', 'chevron', 'fleche', 'flèche',
                        'nav', 'menu', 'emoji', 'icone', 'icône', 'bouton',
                        'haut', 'bas', 'gauche', 'droite', 'suivant', 'precedent',
                        'cercle', 'circle', 'round', 'rond', 'symbole', 'symbol',
                        # Specific icon types
                        'lightbulb', 'ampoule', 'bulb', 'lamp', 'lampe', 'ampoule',
                        'placeholder', 'place-holder', 'generic', 'generique',
                        'plus sign', 'signe plus', 'add icon', 'icone ajout',
                        'magnifying glass', 'loupe', 'search icon', 'icone recherche',
                        'thumbs up', 'thumbs down', 'pouce', 'camera icon', 'icone camera',
                        'speech bubble', 'bulle de dialogue', 'double arrow', 'resize',
                        # Person/people icons
                        'person icon', 'icone personne', 'icone utilisateur', 'icone profil',
                        'silhouette', 'avatar', 'tête', 'épaules', 'head icon', 'shoulder icon',
                        # Checkmark/verification icons
                        'checkmark', 'check icon', 'icone check', 'icone vérification',
                        'tick', 'coche', 'verification icon', 'icone verification',
                        # Remuneration/payment icons
                        'remuneration', 'rémunération', 'payment icon', 'icone paiement',
                        'money icon', 'icone argent', 'hand money', 'main argent',
                        'salary icon', 'icone salaire',
                        # Feedback icons (thumbs up/down) - STRICT FILTERING
                        'thumbs up', 'thumbs down', 'thumbs-up', 'thumbs-down',
                        'thumbsup', 'thumbsdown', 'thumb up', 'thumb down',
                        'like button', 'dislike button', 'feedback button',
                        'pouce', 'pouce-haut', 'pouce-bas', 'pouce vers le haut', 'pouce vers le bas',
                        'like icon', 'dislike icon', 'feedback icon', 'icone feedback',
                        'icone pouce', 'icone like', 'icone dislike',
                        # Document/folder icons (NOT screenshots) - STRICT FILTERING
                        'document icon', 'folder icon', 'file icon', 'dossier icon',
                        'cv icon', 'resume icon', 'document with', 'folder with',
                        'document cv', 'icone document', 'icone dossier', 'icone fichier',
                        'icone cv', 'document avec loupe', 'dossier avec loupe',
                        'document with magnifying', 'folder with magnifying',
                        # Warning/stop sign icons - STRICT FILTERING
                        'stop sign', 'stop signal', 'panneau arret', 'panneau arrêt',
                        'panneau stop', 'stop icon', 'icone stop', 'icone arret', 'icone arrêt',
                        'warning sign', 'panneau avertissement', 'warning icon', 'icone warning',
                        'icone avertissement', 'alert sign', 'panneau alerte', 'alert icon',
                        'icone alerte', 'danger sign', 'panneau danger', 'danger icon',
                        'icone danger', 'attention sign', 'panneau attention', 'attention icon',
                        'icone attention', 'octagon', 'octogone', 'red stop', 'arret rouge',
                        'arrêt rouge', 'hand stop', 'main stop', 'stop hand'
                    ]
                    is_icon_text = any(pattern in combined_text for pattern in icon_text_patterns)
                    
                    # Detect simple icon patterns (circle with symbol, lightbulb, plus sign, etc.)
                    # These are often described as "cercle vert", "green circle", "ampoule", etc.
                    simple_icon_patterns = [
                        'cercle', 'circle', 'rond', 'round',
                        'symbole', 'symbol', 'signe', 'sign',
                        'icone', 'icon', 'bouton', 'button',
                        'lightbulb', 'ampoule', 'bulb', 'lamp', 'lampe',
                        'plus sign', 'signe plus', 'add icon', 'icone ajout',
                        'placeholder', 'place-holder', 'generic', 'generique',
                        # Person/people icons
                        'person', 'people', 'user', 'utilisateur', 'profil', 'profile',
                        'head', 'shoulder', 'silhouette', 'avatar', 'tête', 'épaules',
                        # Checkmark/verification icons
                        'checkmark', 'check', 'verification', 'vérification', 'tick', 'coche',
                        # Remuneration/payment icons
                        'remuneration', 'rémunération', 'payment', 'paiement', 'money', 'argent',
                        'cash', 'hand', 'main', 'salary', 'salaire'
                    ]
                    # If the description is very short and contains icon patterns, it's likely an icon
                    is_simple_icon = False
                    if len(combined_text) < 80:  # Short description (increased from 50 to 80)
                        if any(pattern in combined_text for pattern in simple_icon_patterns):
                            # Check if it's NOT explicitly a screenshot
                            if not any(x in combined_text for x in ['screenshot', 'capture', 'interface', 'fenetre', 'ecran', 'affichage', 'window', 'dialog', 'application', 'logiciel']):
                                is_simple_icon = True
                    
                    # Additional check: Exclude images that are too square (icons are often square or near-square)
                    # Real screenshots have a width/height ratio significantly different from 1.0
                    is_near_square = False
                    if width_val and height_val and width_val > 0 and height_val > 0:
                        ratio = max(width_val, height_val) / min(width_val, height_val)
                        # If ratio is close to 1.0 (square or near-square) and image is not very large, likely an icon
                        if 0.9 <= ratio <= 1.1:  # Within 10% of square
                            if width_val < 300:  # And not very large
                                is_near_square = True
                    
                    # STRICT FILTERING: Skip if it's clearly an icon/logo/arrow/emoji
                    # Only allow if it's explicitly a screenshot/interface image
                    if is_small_icon or is_square_icon or is_simple_icon or is_near_square:
                        # Small images, square icons, simple icons, or near-square images are almost always icons, unless explicitly marked as screenshot
                        if not any(x in img_filename or x in combined_text for x in ['screenshot', 'capture', 'interface', 'fenetre', 'ecran', 'affichage', 'window', 'dialog', 'application', 'logiciel']):
                            continue
                    
                    if is_icon_filename:
                        # Filename suggests icon/arrow - only allow if explicitly a screenshot
                        if not any(x in img_filename for x in ['screenshot', 'capture', 'interface', 'fenetre', 'ecran', 'affichage', 'window', 'dialog', 'images/']):
                            continue
                    
                    if is_icon_text:
                        # Alt/title suggests icon/arrow - only allow if explicitly a screenshot
                        if not any(x in combined_text for x in ['screenshot', 'capture', 'interface', 'fenetre', 'ecran', 'affichage', 'window', 'dialog']):
                            continue
                    
                    # STRICT REQUIREMENT: Only include images that are EXPLICITLY screenshots:
                    # - Must be in /images/ directory (where screenshots are typically stored)
                    # - AND must NOT be square/near-square (screenshots are rectangular)
                    # - AND must have explicit screenshot keywords in filename/description
                    # - OR have screenshot keywords in context/caption
                    is_likely_screenshot = False
                    
                    # Priority 1: Images in /images/ directory (most reliable indicator)
                    # BUT exclude if they're square/near-square (likely icons even in /images/)
                    if '/images/' in img_url.lower() and not is_icon_filename:
                        # Additional check: exclude square/near-square images even from /images/
                        if width_val and height_val and width_val > 0 and height_val > 0:
                            ratio = max(width_val, height_val) / min(width_val, height_val)
                            # Only accept if it's NOT square/near-square (ratio > 1.2 means significantly rectangular)
                            if ratio > 1.2 or width_val >= 400:  # Rectangular OR very large (likely a real screenshot)
                                is_likely_screenshot = True
                        else:
                            # No dimensions available, trust /images/ directory
                            is_likely_screenshot = True
                    
                    # Priority 2: Explicit screenshot keywords in filename
                    screenshot_filename_keywords = ['screenshot', 'capture', 'interface', 'fenetre', 'ecran', 'affichage', 'window', 'dialog', 'ecran']
                    if any(keyword in img_filename for keyword in screenshot_filename_keywords):
                        is_likely_screenshot = True
                    
                    # Priority 3: Screenshot keywords in alt/title
                    if any(keyword in combined_text for keyword in screenshot_filename_keywords):
                        is_likely_screenshot = True
                    
                    # Priority 4: Screenshot keywords in context
                    if context_text and any(keyword in context_text.lower() for keyword in ['capture', 'screenshot', 'interface', 'fenetre', 'ecran', 'affichage', 'window', 'dialog']):
                        is_likely_screenshot = True
                    
                    # Priority 5: Screenshot keywords in figure caption
                    if figure_caption and any(keyword in figure_caption.lower() for keyword in ['capture', 'screenshot', 'interface', 'fenetre', 'ecran', 'affichage', 'window', 'dialog']):
                        is_likely_screenshot = True
                    
                    # STRICT: Skip if it doesn't look like a screenshot
                    if not is_likely_screenshot:
                        continue
                    
                    # Additional check: Exclude SVG files (almost always icons/vectors)
                    if img_url.lower().endswith('.svg'):
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
                    # Only PNG, JPG, JPEG, WEBP - exclude GIF (often animated icons/emojis)
                    if any(img_url.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
                        images.append({
                            "url": img_url,
                            "alt": alt_text or 'Screenshot',
                            "title": title_text or '',
                            "description": enhanced_description,  # Enhanced description with context
                            "context": context_text,  # Context around the image
                            "caption": figure_caption,  # Figure caption if available
                            "width": width_val,  # Store dimensions for later filtering
                            "height": height_val,
                            "source_url": url  # Store the page URL where this image was found
                        })
            
            title = soup.title.string if soup.title else url
            # Ensure title is properly encoded
            if isinstance(title, bytes):
                title = title.decode('utf-8', errors='ignore')
            elif title:
                title = str(title).encode('utf-8', errors='ignore').decode('utf-8')
            
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
    # Start from base URL
    scrape_page(BASE_URL)
    
    # Also try to access known important pages directly
    # Some pages might not be linked from the main page
    known_pages = [
        "dlg103.html",  # Créer un utilisateur et l'affecter à un groupe
        "dlg104.html",  # Other common dialogs
    ]
    
    for page in known_pages:
        full_url = urljoin(BASE_URL, page)
        if full_url not in visited_urls:
            logger.info(f"Trying to access known page: {full_url}")
            scrape_page(full_url)
    
    logger.info(f"Scraping complete. Found {len(pages_content)} pages.")
    return pages_content

if __name__ == "__main__":
    data = run_scraper()
    # Save for inspection
    import json
    with open("scraped_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
