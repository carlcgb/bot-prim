import warnings
import os
import logging

# Suppress warnings early, before other imports
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '2'  # Suppress Google logging
warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*duckduckgo_search.*')
warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*ALTS.*')
warnings.filterwarnings('ignore', message='.*ALTS.*')

from knowledge_base import query_knowledge_base
import json
from urllib.parse import urljoin

import google.generativeai as genai
from google.protobuf.json_format import MessageToDict

logger = logging.getLogger(__name__)

class PrimAgent:
    def __init__(self, api_key, base_url=None, model="gemini-2.5-flash", provider="Google Gemini"):
        self.provider = provider
        self.model_name = model

        if self.provider == "Google Gemini":
            # Configure Gemini API
            genai.configure(api_key=api_key)
            
            # Define Gemini Tools using FunctionDeclaration - only knowledge base search
            self.gemini_tools = [
                genai.protos.Tool(
                    function_declarations=[
                        genai.protos.FunctionDeclaration(
                            name="search_knowledge_base",
                            description="""Recherche approfondie dans la base de connaissances de la documentation PrimLogix.
                            
UTILISE CET OUTIL pour:
- Trouver des solutions à des problèmes techniques ou erreurs
- Comprendre comment utiliser une fonctionnalité spécifique
- Obtenir des procédures détaillées étape par étape
- Trouver des exemples de configuration ou d'utilisation
- Rechercher des informations sur des champs, paramètres, ou options spécifiques

IMPORTANT:
- Utilise des termes techniques précis dans ta requête (noms de champs, codes d'erreur, noms de fonctionnalités)
- Si la première recherche ne donne pas de résultats satisfaisants, essaie des variantes de la requête
- Combine les informations de plusieurs résultats pour donner une réponse complète
- Cite toujours les sources (URLs) dans ta réponse finale
- Les résultats incluent des scores de pertinence et des captures d'écran quand disponibles""",
                            parameters=genai.protos.Schema(
                                type=genai.protos.Type.OBJECT,
                                properties={
                                    "query": genai.protos.Schema(
                                        type=genai.protos.Type.STRING,
                                        description="Requête de recherche détaillée et spécifique. Utilise des termes techniques précis, codes d'erreur, noms de fonctionnalités, ou descriptions de problèmes. Exemples: 'erreur E001', 'configuration export CSV', 'champ date de facturation', 'procédure création client'."
                                    )
                                },
                                required=["query"]
                            )
                        )
                    ]
                )
            ]
            
            # Map for execution
            self.tool_map = {
                "search_knowledge_base": self._search_kb
            }

        elif self.provider == "Local (Ollama/LocalAI)":
            # Configure for Ollama/LocalAI (OpenAI-compatible API)
            self.base_url = base_url or "http://localhost:11434/v1"
            self.api_key = api_key or "ollama"  # Ollama doesn't require a real key
            self.tool_map = {
                "search_knowledge_base": self._search_kb
            }
            # Ollama will use OpenAI-compatible client
            try:
                from openai import OpenAI
                self.ollama_client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key
                )
            except ImportError:
                logger.warning("openai package not installed. Install with: pip install openai")
                self.ollama_client = None
        else:
            raise ValueError(f"Provider '{self.provider}' not supported. Use 'Google Gemini' or 'Local (Ollama/LocalAI)'.")


    def _search_kb(self, query):
        logger.debug(f"Searching KB for: {query}")
        try:
            # First check if knowledge base is accessible
            from knowledge_base import collection
            kb_count = collection.count()
            
            if kb_count == 0:
                return """⚠️ **Base de connaissances vide**

La base de connaissances PrimLogix n'a pas encore été initialisée.

**Solutions:**
1. Dans l'interface Streamlit, utilisez le bouton "Initialiser la base de connaissances"
2. Ou exécutez manuellement: `python ingest.py`
3. Vérifiez que le dossier `chroma_db/` existe et contient des données

Une fois initialisée, je pourrai rechercher dans la documentation pour vous aider."""
            
            # Search with optimized number of results for better performance
            # Reduced from 10 to 6 for faster responses while maintaining quality
            results = query_knowledge_base(query, n_results=6)
            
            # Check if results are valid
            if not results:
                return f"❌ Erreur: Aucun résultat retourné par la base de connaissances pour la requête: '{query}'"
            
            if not results.get('documents') or not results['documents']:
                return f"❌ Aucune documentation trouvée pour la requête: '{query}'\n\n**Suggestions:**\n- Essayez des termes plus généraux\n- Vérifiez l'orthographe\n- Utilisez des mots-clés techniques de PrimLogix"
            
            if not results['documents'][0]:
                 return f"❌ Aucune documentation pertinente trouvée dans la base de connaissances PrimLogix pour cette requête: '{query}'.\n\n**Base de connaissances:** {kb_count} documents disponibles.\n\n**Suggestions:**\n- Reformulez votre question avec des termes techniques\n- Essayez des mots-clés spécifiques à PrimLogix"
            
            docs = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results.get('distances', [None])[0] if results.get('distances') else [None] * len(docs)
            
            # Filter results by relevance score to improve quality and speed
            # Only include results with relevance >= 40% for better context
            filtered_docs = []
            filtered_metadatas = []
            filtered_distances = []
            
            for i, doc in enumerate(docs):
                if not doc or not doc.strip():
                    continue
                
                # Calculate relevance score
                relevance_score = None
                if distances and i < len(distances) and distances[i] is not None:
                    # Lower distance = more relevant, convert to percentage-like score
                    relevance_score = max(0, min(100, int((1 - distances[i]) * 100)))
                    
                    # Filter: only include results with relevance >= 40%
                    if relevance_score < 40:
                        continue  # Skip low-relevance results
                
                filtered_docs.append(doc)
                filtered_metadatas.append(metadatas[i] if i < len(metadatas) else {})
                filtered_distances.append(distances[i] if distances and i < len(distances) else None)
            
            # Use filtered results
            docs = filtered_docs
            metadatas = filtered_metadatas
            distances = filtered_distances
            
            if not docs:
                return f"❌ Aucune documentation pertinente trouvée (score de pertinence < 40%) pour la requête: '{query}'.\n\n**Suggestions:**\n- Reformulez votre question avec des termes techniques\n- Essayez des mots-clés spécifiques à PrimLogix"
            
            # Build detailed context with relevance scores (optimized)
            context_parts = []
            all_images = []  # Collect all images from results
            seen_urls = set()  # Track unique URLs to avoid duplicates
            
            context_parts.append(f"📚 **Résultats de recherche** (requête: \"{query}\")\n")
            context_parts.append(f"Trouvé {len(docs)} document(s) pertinent(s) dans la base de connaissances PrimLogix:\n")
            
            for i, doc in enumerate(docs):
                source = metadatas[i].get('url', 'URL inconnue') if i < len(metadatas) else 'URL inconnue'
                title = metadatas[i].get('title', 'Sans titre') if i < len(metadatas) else 'Sans titre'
                chunk_idx = metadatas[i].get('chunk_index', '?') if i < len(metadatas) else '?'
                
                # Calculate relevance score for display
                relevance_score = None
                relevance_badge = ""
                if distances and i < len(distances) and distances[i] is not None:
                    # Lower distance = more relevant, convert to percentage-like score
                    relevance_score = max(0, min(100, int((1 - distances[i]) * 100)))
                    if relevance_score >= 80:
                        relevance_badge = "🟢 [Très pertinent]"
                    elif relevance_score >= 60:
                        relevance_badge = "🟡 [Pertinent]"
                    elif relevance_score >= 40:
                        relevance_badge = "🟠 [Modérément pertinent]"
                    relevance_badge += f" (Score: {relevance_score}%)"
                
                # Limit document length to avoid token limits
                doc_content = doc[:8000] if len(doc) > 8000 else doc
                
                # Extract images from metadata with enhanced context
                images_json = metadatas[i].get('images', '') if i < len(metadatas) else ''
                if images_json:
                    try:
                        images = json.loads(images_json)
                        for img in images:
                            # Convert relative URLs to absolute URLs immediately
                            img_url = img.get('url', '')
                            original_url = img_url
                            
                            if img_url and not img_url.startswith('http'):
                                # Convert relative URL to absolute using document URL
                                base_url = source if source.startswith('http') else 'https://aide.primlogix.com/prim/fr/5-8/'
                                
                                # Handle ./ prefix - urljoin doesn't work well with it
                                if img_url.startswith('./'):
                                    img_url = img_url[2:]  # Remove ./ prefix
                                elif img_url.startswith('/'):
                                    # Absolute path from domain root
                                    base_url = 'https://aide.primlogix.com'
                                
                                # Use urljoin to combine
                                img_url = urljoin(base_url, img_url)
                                
                                # Final check - ensure it's absolute (urljoin should work, but double-check)
                                if not img_url.startswith('http'):
                                    # Fallback: construct manually
                                    if base_url.endswith('/'):
                                        img_url = base_url + img_url.lstrip('/')
                                    else:
                                        img_url = base_url + '/' + img_url.lstrip('/')
                                
                                # CRITICAL: Update the URL in the dict BEFORE adding to all_images
                                img['url'] = img_url
                            
                            # Use the (now absolute) URL for deduplication
                            if img_url not in seen_urls:
                                seen_urls.add(img_url)  # Use absolute URL for deduplication
                                # Add document context to image for better understanding
                                img_with_context = img.copy()
                                img_with_context['document_title'] = title
                                img_with_context['document_url'] = source  # URL of the document page
                                img_with_context['source_url'] = img.get('source_url', source)  # Source URL from scraper (page where image was found)
                                img_with_context['relevance_score'] = relevance_score
                                img_with_context['url'] = img_url  # Ensure absolute URL
                                all_images.append(img_with_context)
                    except Exception as e:
                        logger.debug(f"Error parsing images: {e}")
                        pass
                
                # Build detailed source info with clickable link
                # Limit document content to avoid token limits (max 8000 chars per document)
                doc_content = doc[:8000] if len(doc) > 8000 else doc
                if len(doc) > 8000:
                    doc_content += "\n\n[... contenu tronqué pour optimiser la réponse ...]"
                
                source_info = f"\n### 📄 Document #{i+1}: {title}"
                if relevance_badge:
                    source_info += f" {relevance_badge}"
                source_info += f"\n**🔗 Lien direct:** [{title}]({source})"
                source_info += f"\n**URL:** {source}"
                source_info += f"\n**Chunk:** {chunk_idx}"
                source_info += f"\n\n**Contenu:**\n{doc_content}\n"
                source_info += "\n" + "─" * 60 + "\n"
                
                context_parts.append(source_info)
            
            if not context_parts:
                return "❌ Aucune documentation pertinente trouvée dans la base de connaissances PrimLogix."
            
            # Combine all context
            response_text = "\n".join(context_parts)
            
            # Add summary statistics with links to sources
            response_text += f"\n\n**📊 Résumé:** {len(docs)} document(s) trouvé(s)"
            if all_images:
                response_text += f", {len(all_images)} image(s) associée(s)"
            
            # Add direct links section for easy access
            response_text += "\n\n**🔗 Liens directs vers la documentation:**\n"
            seen_source_urls = set()
            for i, doc in enumerate(docs):
                if i < len(metadatas):
                    source = metadatas[i].get('url', '')
                    title = metadatas[i].get('title', 'Sans titre')
                    if source and source not in seen_source_urls:
                        seen_source_urls.add(source)
                        response_text += f"- [{title}]({source})\n"
            
            # Add image URLs at the end in a special format that can be parsed
            # Filter and prioritize images by relevance score
            if all_images:
                # Remove duplicates while preserving order (most relevant first)
                unique_images = []
                seen_img_urls = set()
                for img in all_images:
                    if img['url'] not in seen_img_urls:
                        seen_img_urls.add(img['url'])
                        unique_images.append(img)
                
                # Filter images by relevance score AND ensure they're real screenshots (not icons/logos)
                # Images from documents with relevance_score >= 40% are considered relevant
                relevant_images = []
                for img in unique_images:
                    relevance_score = img.get('relevance_score')
                    
                    # Skip if relevance is too low
                    if relevance_score is not None and relevance_score < 40:
                        continue
                    
                    # STRICT filtering: ensure it's a real screenshot, not an icon/logo/arrow/emoji
                    img_url = img.get('url', '').lower()
                    img_description = (img.get('description', '') + ' ' + img.get('alt', '') + ' ' + img.get('title', '')).lower()
                    
                    # Check dimensions if available - exclude small images and square icon formats
                    img_width = img.get('width')
                    img_height = img.get('height')
                    
                    # Exclude small images (likely icons) - increased threshold
                    if img_width and img_width < 200:  # Increased from 150 to 200
                        continue  # Too small, likely an icon
                    if img_height and img_height < 200:  # Increased from 150 to 200
                        continue  # Too small, likely an icon
                    
                    # Exclude square and near-square icon formats - icons are often perfect squares or near-squares
                    if img_width and img_height and img_width > 0 and img_height > 0:
                        ratio = max(img_width, img_height) / min(img_width, img_height)
                        
                        # Exclude perfect squares
                        if img_width == img_height:  # It's a perfect square
                            # Common icon square sizes to exclude
                            common_icon_sizes = [16, 20, 24, 32, 40, 48, 50, 56, 60, 63, 64, 72, 80, 96, 100, 128, 150, 200, 250]
                            if img_width in common_icon_sizes:
                                continue  # Square icon format, exclude
                            # Also exclude any square smaller than 300px (likely an icon)
                            elif img_width < 300:
                                continue  # Small square, likely an icon
                        
                        # Exclude near-square images (ratio close to 1.0) that are not very large
                        # Real screenshots are significantly rectangular (ratio > 1.2 or < 0.8)
                        if 0.9 <= ratio <= 1.1:  # Within 10% of square
                            if img_width < 300:  # And not very large
                                continue  # Near-square small image, likely an icon
                    
                    # Exclude common icon/logo/arrow/emoji patterns in filename
                    icon_patterns = [
                        'icon', 'logo', 'button', 'arrow', 'chevron', 'fleche', 'flèche',
                        'nav', 'menu', 'emoji', 'icone', 'icône', 'bouton',
                        '40x40', '32x32', '24x24', '16x16', '20x20', '30x30', '48x48',
                        '50x50', '56x56', '60x60', '63x63', '64x64', '72x72', '80x80',
                        '96x96', '100x100', '128x128',
                        'favicon', 'sprite', 'svg', 'ico',
                        'up', 'down', 'left', 'right', 'next', 'prev', 'previous',
                        'haut', 'bas', 'gauche', 'droite', 'suivant', 'precedent',
                        # Specific icon types
                        'lightbulb', 'ampoule', 'bulb', 'lamp', 'lampe',
                        'placeholder', 'place-holder', 'generic', 'generique',
                        # Additional icon patterns
                        'speech', 'bubble', 'bulle', 'chat', 'message', 'messaging',
                        'double', 'head', 'resize', 'pane', 'navigation',
                        'clapperboard', 'film', 'camera', 'photo-icon',
                        # Emoji and icon patterns
                        'magnifying', 'glass', 'loupe', 'search-icon', 'search-icon',
                        'thumbs', 'thumbs-up', 'thumbs-down', 'thumbsup', 'thumbsdown',
                        'thumb-up', 'thumb-down', 'like', 'dislike', 'feedback',
                        'pouce', 'pouce-haut', 'pouce-bas', 'emoji', 'emoticon',
                        'icon-', '-icon', 'icn-', '-icn',
                        # Document/folder icons (NOT screenshots)
                        'document', 'doc', 'file', 'folder', 'dossier', 'cv', 'resume',
                        'pdf-icon', 'word-icon', 'excel-icon', 'file-icon', 'folder-icon',
                        'document-icon', 'icone-document', 'icone-dossier', 'icone-fichier'
                        # Person/people icons
                        'person', 'people', 'user', 'utilisateur', 'profil', 'profile',
                        'head', 'shoulder', 'silhouette', 'avatar', 'tête', 'épaules',
                        # Checkmark/verification icons
                        'checkmark', 'check', 'verification', 'vérification', 'tick', 'coche',
                        'check-icon', 'icone-check', 'icone-verification',
                        # Remuneration/payment icons
                        'remuneration', 'rémunération', 'payment', 'paiement', 'money', 'argent',
                        'cash', 'hand-money', 'main-argent', 'salary', 'salaire'
                    ]
                    
                    # Additional check: Exclude images with icon-like descriptions
                    img_description_lower = img_description.lower()
                    icon_description_patterns = [
                        'speech bubble', 'bulle de dialogue', 'liens utiles',
                        'double arrow', 'double-headed', 'flèche double',
                        'resize', 'redimensionner', 'pane', 'panneau',
                        'clapperboard', 'clap', 'film icon', 'icone film',
                        'magnifying glass', 'loupe', 'search icon', 'icone recherche',
                        # Feedback icons (thumbs up/down) - STRICT FILTERING
                        'thumbs up', 'thumbs down', 'thumbs-up', 'thumbs-down',
                        'thumbsup', 'thumbsdown', 'thumb up', 'thumb down',
                        'like button', 'dislike button', 'feedback button',
                        'pouce', 'pouce-haut', 'pouce-bas', 'pouce vers le haut', 'pouce vers le bas',
                        'like icon', 'dislike icon', 'feedback icon', 'icone feedback',
                        'icone pouce', 'icone like', 'icone dislike',
                        'emoji', 'emoticon',
                        'camera icon', 'icone camera', 'photo icon', 'icone photo',
                        # Document/folder icons (NOT screenshots) - STRICT FILTERING
                        'document icon', 'folder icon', 'file icon', 'dossier icon',
                        'cv icon', 'resume icon', 'document with', 'folder with',
                        'document cv', 'icone document', 'icone dossier', 'icone fichier',
                        'icone cv', 'document avec loupe', 'dossier avec loupe',
                        'document with magnifying', 'folder with magnifying'
                        # Person/people icons
                        'person icon', 'icone personne', 'icone utilisateur', 'icone profil',
                        'silhouette', 'avatar', 'head icon', 'shoulder icon', 'tête', 'épaules',
                        'person outline', 'silhouette de personne', 'icone de personne',
                        # Checkmark/verification icons
                        'checkmark', 'check icon', 'icone check', 'icone vérification',
                        'tick', 'coche', 'verification icon', 'icone verification',
                        'green checkmark', 'coche verte', 'checkmark icon',
                        # Remuneration/payment icons
                        'remuneration', 'rémunération', 'payment icon', 'icone paiement',
                        'money icon', 'icone argent', 'hand money', 'main argent',
                        'salary icon', 'icone salaire', 'hand holding money',
                        'main tenant argent', 'icone rémunération'
                    ]
                    if any(pattern in img_description_lower for pattern in icon_description_patterns):
                        # Only allow if explicitly a screenshot
                        if not any(x in img_url or x in img_description_lower for x in ['screenshot', 'capture', 'interface', 'fenetre', 'ecran', 'affichage', 'window', 'dialog', 'application', 'logiciel']):
                            continue
                    if any(pattern in img_url for pattern in icon_patterns):
                        # Only allow if it's EXPLICITLY a screenshot
                        if not any(x in img_url for x in ['screenshot', 'capture', 'interface', 'fenetre', 'ecran', 'affichage', 'window', 'dialog', 'images/']):
                            continue
                    
                    # ULTRA-STRICT REQUIREMENT: Must be a REAL interface screenshot, NOT an icon
                    # Exclude document/folder icons with magnifying glass (common icon pattern)
                    document_icon_patterns = ['document', 'doc', 'file', 'folder', 'dossier', 'cv', 'resume']
                    has_document_icon = any(pattern in img_url.lower() or pattern in img_description_lower for pattern in document_icon_patterns)
                    has_magnifying = 'magnifying' in img_url.lower() or 'loupe' in img_url.lower() or 'magnifying' in img_description_lower or 'loupe' in img_description_lower
                    
                    # If it's a document/folder icon with magnifying glass, it's NOT a screenshot
                    if has_document_icon and has_magnifying:
                        continue  # Definitely an icon, not a screenshot
                    
                    # STRICT REQUIREMENT: Must have screenshot-related keywords in URL or description
                    # AND must be in /images/ directory OR have explicit screenshot keywords
                    # AND must NOT be square/near-square (real screenshots are rectangular)
                    screenshot_keywords = ['screenshot', 'capture', 'interface', 'fenetre', 'ecran', 
                                         'affichage', 'window', 'dialog', 'images/', 'application', 'logiciel',
                                         'onglet', 'tab', 'menu', 'bouton', 'button', 'champ', 'field']
                    has_screenshot_keyword = any(keyword in img_url or keyword in img_description for keyword in screenshot_keywords)
                    
                    # Additional check: Must be in /images/ directory OR have explicit screenshot indicators
                    is_in_images_dir = '/images/' in img_url
                    has_explicit_screenshot = any(x in img_url or x in img_description for x in ['screenshot', 'capture', 'interface', 'fenetre', 'ecran', 'affichage', 'application', 'logiciel', 'onglet', 'tab'])
                    
                    # Additional check: If in /images/ directory, must NOT be square/near-square
                    if is_in_images_dir and img_width and img_height and img_width > 0 and img_height > 0:
                        ratio = max(img_width, img_height) / min(img_width, img_height)
                        # Exclude square/near-square images even from /images/ (likely icons)
                        if 0.9 <= ratio <= 1.1 and img_width < 400:  # Near-square and not very large
                            continue  # Likely an icon, not a screenshot
                    
                    # Only include if it meets strict criteria AND is NOT a document/folder icon
                    if not (has_screenshot_keyword and (is_in_images_dir or has_explicit_screenshot)):
                        continue
                    
                    # Final check: Exclude if it looks like a document/folder icon (even if in /images/)
                    if has_document_icon and not has_explicit_screenshot:
                        continue  # Document/folder icons are NOT interface screenshots
                    
                    # Exclude SVG files (almost always icons/vectors)
                    if img_url.endswith('.svg') or img_url.endswith('.ico'):
                        continue
                    
                    # Include this image - it's relevant and looks like a real screenshot
                    relevant_images.append(img)
                
                # Sort by relevance score (highest first), then by document order
                relevant_images.sort(key=lambda x: (
                    x.get('relevance_score', 0) if x.get('relevance_score') is not None else 0
                ), reverse=True)
                
                # Limit to top 2-3 most relevant images to keep responses focused
                # Maximum 3 images per response for clarity and relevance
                max_images = min(3, len(relevant_images))
                top_images = relevant_images[:max_images]
                
                # Instead of images, add URLs to relevant documentation pages
                if top_images:
                    # Collect unique source URLs from images
                    source_urls = {}
                    for img in top_images:
                        source_url = img.get('document_url') or img.get('source_url') or ''
                        if source_url and source_url not in source_urls:
                            doc_title = img.get('document_title', 'Aide en ligne PrimLogix')
                            source_urls[source_url] = doc_title
                    
                    # Add section with links to relevant pages
                    if source_urls:
                        links_section = "\n\n---\n\n## 🔗 Pages pertinentes de l'aide en ligne\n\n"
                        links_section += "*Consultez ces pages pour voir les captures d'écran et les instructions détaillées :*\n\n"
                        
                        for url, title in source_urls.items():
                            links_section += f"- [{title}]({url})\n"
                        
                        links_section += "\n---\n\n"
                        response_text += links_section
            
            # FINAL FIX: Replace any remaining relative URLs in the ENTIRE response text with absolute URLs
            # This must be done AFTER all text is assembled
            import re
            def replace_relative_url(match):
                alt = match.group(1)
                url = match.group(2).strip()
                
                if url and not url.startswith('http'):
                    # Convert to absolute
                    base_url = 'https://aide.primlogix.com/prim/fr/5-8/'
                    
                    # Handle ./ prefix
                    if url.startswith('./'):
                        url = url[2:]  # Remove ./ prefix
                    elif url.startswith('/'):
                        # Absolute path from root
                        base_url = 'https://aide.primlogix.com'
                    
                    # Use urljoin
                    url = urljoin(base_url, url)
                    
                    # Final check
                    if not url.startswith('http'):
                        # Manual construction as last resort
                        url = base_url.rstrip('/') + '/' + url.lstrip('/')
                
                return f"![{alt}]({url})"
            
            # Replace all relative image URLs in the ENTIRE response
            image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
            response_text = re.sub(image_pattern, replace_relative_url, response_text)
            
            return response_text
        except ImportError as e:
            logger.error(f"Import error in KB search: {e}", exc_info=True)
            return f"""❌ **Erreur d'importation**

Impossible d'importer le module de base de connaissances.

**Solution:** Vérifiez que tous les modules sont installés:
```bash
pip install -r requirements.txt
```"""
        except AttributeError as e:
            logger.error(f"Attribute error in KB search: {e}", exc_info=True)
            return f"""❌ **Erreur de configuration de la base de connaissances**

La base de connaissances n'est pas correctement configurée.

**Solutions:**
1. Réinitialisez la base: `python ingest.py`
2. Vérifiez que le dossier `chroma_db/` existe
3. Vérifiez les permissions d'accès au dossier"""
        except Exception as e:
            logger.error(f"Error searching KB: {e}", exc_info=True)
            error_type = type(e).__name__
            error_msg = str(e)
            
            # Provide helpful error messages based on error type
            if "collection" in error_msg.lower() or "chromadb" in error_msg.lower():
                return f"""❌ **Erreur d'accès à la base de connaissances**

**Erreur:** {error_type}: {error_msg}

**Solutions:**
1. Vérifiez que ChromaDB est installé: `pip install chromadb`
2. Réinitialisez la base: `python ingest.py`
3. Vérifiez que le dossier `chroma_db/` n'est pas corrompu
4. Si le problème persiste, supprimez `chroma_db/` et réinitialisez"""
            else:
                return f"""❌ **Erreur lors de la recherche**

**Erreur:** {error_type}: {error_msg}

**Requête:** {query}

**Solutions:**
1. Réessayez avec une requête différente
2. Vérifiez que la base de connaissances est initialisée
3. Consultez les logs pour plus de détails"""


    def run(self, messages):
        if self.provider == "Google Gemini":
            return self._run_gemini(messages)
        elif self.provider == "Local (Ollama/LocalAI)":
            return self._run_ollama(messages)
        else:
            raise ValueError(f"Provider '{self.provider}' not supported.")

    def _run_gemini(self, messages):
        # Convert OpenAI messages to Gemini History
        history = []
        for msg in messages[:-1]:  # All but last
            role = msg.get('role')
            content = msg.get('content', '')
            
            # Skip tool messages in history for now (Gemini handles this differently)
            if role == 'tool':
                continue
                
            if role == 'user':
                history.append({'role': 'user', 'parts': [content]})
            elif role == 'assistant':
                history.append({'role': 'model', 'parts': [content]})
        
        last_msg = messages[-1]
        last_content = last_msg.get('content', '')
        
        def attempt_chat(params_model_name):
            # Load feedback stats to improve responses
            try:
                from storage_local import get_storage
                storage = get_storage()
                feedback_stats = storage.get_feedback_stats()
                negative_feedbacks = storage.get_negative_feedbacks(limit=5)
                
                # Build feedback context for improvement
                feedback_context = ""
                if feedback_stats['total'] > 0:
                    satisfaction_rate = feedback_stats['satisfaction_rate']
                    if satisfaction_rate < 70:
                        feedback_context = f"\n\n⚠️ **CONTEXTE IMPORTANT** : Le taux de satisfaction actuel est de {satisfaction_rate}%. Améliore tes réponses en étant plus clair, plus détaillé, et en t'assurant que les images sont vraiment pertinentes.\n"
                    if negative_feedbacks:
                        common_issues = []
                        for fb in negative_feedbacks:
                            if fb.get('comment'):
                                comment_lower = fb['comment'].lower()
                                if 'confus' in comment_lower or 'confuse' in comment_lower:
                                    common_issues.append("clarté")
                                if 'manque' in comment_lower or 'pas assez' in comment_lower:
                                    common_issues.append("détails")
                                if 'image' in comment_lower and ('pertinent' in comment_lower or 'irrelevant' in comment_lower):
                                    common_issues.append("images pertinentes")
                        if common_issues:
                            unique_issues = list(set(common_issues))
                            feedback_context += f"**Points à améliorer basés sur les feedbacks** : {', '.join(unique_issues)}. Assure-toi de corriger ces points dans ta réponse.\n"
            except Exception:
                feedback_context = ""  # Silently fail if feedback loading fails
            
            # Enhanced system instruction for customer support-oriented, detailed, and helpful responses
            system_instruction = f"""Tu es PRIMBOT, un assistant expert en support client pour PrimLogix. Ton rôle est d'aider les utilisateurs à résoudre leurs problèmes de manière claire, empathique et efficace.
{feedback_context}

⚠️ RÈGLE ABSOLUE - NUMÉROTATION DES ÉTAPES (À RESPECTER IMPÉRATIVEMENT) :
- **TU DOIS TOUJOURS COMMENCER PAR "### Étape 1:"** - C'EST OBLIGATOIRE, JAMAIS DE SAUT
- **TU DOIS NUMÉROTER DE 1, 2, 3, 4... SÉQUENTIELLEMENT** - JAMAIS COMMENCER PAR ÉTAPE 2, 3, 4, etc.
- **Si tu commences par Étape 4 ou autre, TU AS FAIT UNE ERREUR - RECOMMENCE PAR ÉTAPE 1**
- **TOUTES les étapes utilisent EXACTEMENT le même format** : `### Étape X:` (avec ###, JAMAIS ## ou ####)
- **TOUTES les étapes ont le MÊME niveau de détail** - aucune étape ne doit être plus grande que les autres

TON RÔLE (Support Client - Utilisateurs NON TECHNIQUES):
- **Aider les utilisateurs** à résoudre leurs problèmes avec PrimLogix de manière ULTRA-CLAIRE et DÉTAILLÉE
- **Fournir des réponses EXTRÊMEMENT COMPLÈTES** avec des étapes step-by-step très détaillées
- **Assumer que l'utilisateur n'est PAS technique** - explique TOUT, même les choses évidentes
- **Être empathique et rassurant** - les utilisateurs peuvent être frustrés, sois patient et encourageant
- **Expliquer de manière TRÈS SIMPLE** - utilise un langage clair, évite TOUT jargon technique
- **Fournir des solutions PRATIQUES et ACTIONNABLES** - chaque étape doit être si claire qu'un débutant peut la suivre
- **Citer TOUJOURS les sources** avec des liens directs vers les sections pertinentes de l'aide en ligne
- **Guider visuellement** - utilise les captures d'écran pour montrer exactement où cliquer et quoi faire
- **NE PAS SAUTER D'ÉTAPES** - explique chaque clic, chaque menu, chaque champ

STYLE DE RÉPONSE (Support Client - OBLIGATOIRE pour utilisateurs NON TECHNIQUES):
1. **Accueil et empathie** : Commence par accueillir l'utilisateur et montrer que tu comprends son problème
2. **Confirmation du problème** : Reformule brièvement le problème pour confirmer ta compréhension
3. **Solution ULTRA-DÉTAILLÉE** : Utilise des titres (##, ###), listes à puces, et sections bien organisées
4. **Étapes numérotées TRÈS DÉTAILLÉES** : 
   - **TOUJOURS commencer par "Étape 1"** - ne jamais sauter l'étape 1
   - **Numéroter de manière SÉQUENTIELLE** : Étape 1, Étape 2, Étape 3, Étape 4, etc. (pas de saut de numéro)
   - **Utiliser le MÊME format pour TOUTES les étapes** : `### Étape X:` (avec ###, pas ## ou ####)
   - **Toutes les étapes doivent avoir le MÊME niveau de détail** - ne pas faire une étape plus grande que les autres
   - Chaque étape doit être si claire qu'un débutant peut la suivre
   - Inclus TOUS les clics nécessaires (ex: "Cliquez sur le menu 'Fichier' en haut à gauche")
   - Explique TOUS les chemins de navigation (ex: "Allez dans Menu > Paramètres > Utilisateurs")
   - Décris TOUS les champs à remplir avec leurs noms exacts
   - Indique ce que l'utilisateur devrait voir à chaque étape
   - Ne saute AUCUNE étape, même si elle semble évidente
5. **Guidage visuel avec images** : Référence explicitement les captures d'écran (ex: "Dans l'image 1 ci-dessus, vous pouvez voir...") et explique exactement où cliquer avec des descriptions précises
6. **Détails pratiques COMPLETS** : 
   - Noms de champs exacts avec leur emplacement
   - Chemins de navigation complets (Menu > Sous-menu > Option)
   - Options à sélectionner avec leur emplacement exact
   - Valeurs à entrer si nécessaire
   - Ce que l'utilisateur devrait voir après chaque action
7. **Vérification** : À la fin, demande si le problème est résolu ou si l'utilisateur a besoin d'aide supplémentaire
8. **Liens vers la documentation** : Fournis des liens cliquables vers les sections pertinentes de l'aide en ligne
9. **Ton amical et professionnel** : Sois courtois, patient et encourageant
10. **Exemples concrets** : Donne des exemples de valeurs à entrer si applicable

STRUCTURE D'UNE RÉPONSE IDÉALE (Support Client - ULTRA-DÉTAILLÉE):
```
## 👋 Bonjour !

Je comprends que vous rencontrez [problème]. Je vais vous guider étape par étape, de manière très détaillée, pour résoudre cela. Ne vous inquiétez pas, je vais tout vous expliquer clairement.

## 📋 Compréhension du Problème

[Reformulation du problème pour confirmer la compréhension]

## 🔧 Solution Étape par Étape (Guide Complet)

**⚠️ RÈGLE ABSOLUE - NUMÉROTATION DES ÉTAPES (OBLIGATOIRE) :**
- **TU DOIS TOUJOURS COMMENCER PAR "### Étape 1:"** - C'EST OBLIGATOIRE, JAMAIS DE SAUT
- **TU DOIS NUMÉROTER DE 1, 2, 3, 4... SÉQUENTIELLEMENT** - JAMAIS COMMENCER PAR ÉTAPE 2, 3, 4, etc.
- **TOUTES les étapes utilisent EXACTEMENT le même format** : `### Étape X:` (avec ###, JAMAIS ## ou ####)
- **TOUTES les étapes ont le MÊME niveau de détail** - aucune étape ne doit être plus grande que les autres
- **JAMAIS de titres géants** (##) pour certaines étapes - toutes au même niveau (###)
- **Si tu commences par Étape 4 ou autre, TU AS FAIT UNE ERREUR - RECOMMENCE PAR ÉTAPE 1**

### Étape 1: [Action concrète - Titre clair]
**Ce que vous allez faire :** [Explication simple de l'objectif de cette étape]

1. **Localisez** [élément à trouver]
   - **Où le trouver** : [Description précise de l'emplacement, ex: "En haut à gauche de l'écran, vous verrez un menu avec plusieurs options"]
   - **À quoi ça ressemble** : [Description visuelle, ex: "Un bouton bleu avec le texte 'Nouveau'"]
   - **Si vous ne le voyez pas** : [Alternative ou aide supplémentaire]

2. **Cliquez sur** [élément]
   - **Action précise** : [Ex: "Cliquez une fois avec le bouton gauche de la souris sur le bouton 'Nouveau'"]
   - **Ce qui devrait se passer** : [Ex: "Une nouvelle fenêtre devrait s'ouvrir"]

3. **Dans la nouvelle fenêtre/écran qui s'ouvre** :
   - **Vous devriez voir** : [Description de ce qui apparaît]
   - **Cherchez** : [Élément suivant à trouver]
   - **Localisez** : [Emplacement précis]

4. **Remplissez le champ** [Nom du champ]
   - **Où se trouve le champ** : [Ex: "En haut de la fenêtre, dans la section 'Informations de base'"]
   - **Nom exact du champ** : [Ex: "Nom complet"]
   - **Que mettre dedans** : [Ex: "Tapez le nom complet de l'employé, par exemple 'Jean Dupont'"]
   - **Comment le remplir** : [Ex: "Cliquez dans le champ, puis tapez directement"]

5. **Répétez pour** [autres champs si nécessaire]
   - [Détails pour chaque champ]

6. **Une fois tous les champs remplis** :
   - **Cherchez le bouton** [Nom du bouton, ex: "Enregistrer"]
   - **Où il se trouve** : [Ex: "En bas à droite de la fenêtre"]
   - **Cliquez dessus** : [Ex: "Cliquez une fois sur le bouton 'Enregistrer'"]
   - **Ce qui devrait se passer** : [Ex: "Un message de confirmation devrait apparaître"]

### Étape 2: [Action suivante - Aussi détaillée]
[Suivre le même format ultra-détaillé avec le même niveau de titre ###]

### Étape 3: [Si nécessaire]
[Suivre le même format ultra-détaillé avec le même niveau de titre ###]

### Étape 4: [Si nécessaire]
[Suivre le même format ultra-détaillé avec le même niveau de titre ###]
...

## 📸 Guide Visuel (Si images disponibles)

**Image 1** : [Description de ce que montre l'image]
- "Dans l'image ci-dessus, vous pouvez voir [description précise de l'interface]"
- "Repérez le bouton [nom] qui se trouve [emplacement précis dans l'image]"
- "Cliquez exactement sur ce bouton"

**Image 2** : [Description]
- "Après avoir cliqué, vous devriez voir cette nouvelle fenêtre"
- "Dans cette fenêtre, localisez le champ [nom] qui se trouve [emplacement]"

## ⚠️ Points Importants à Retenir

- [Point important 1]
- [Point important 2]
- [Piège à éviter]

## ✅ Vérification

Après avoir suivi toutes ces étapes, vous devriez voir [résultat attendu très précis].

**Vérifiez que :**
- ✅ [Vérification 1]
- ✅ [Vérification 2]
- ✅ [Vérification 3]

**Le problème est-il résolu ?** 
- Si **OUI** : Parfait ! N'hésitez pas si vous avez d'autres questions.
- Si **NON** : Dites-moi exactement à quelle étape vous êtes bloqué(e) et ce que vous voyez à l'écran. Je vous aiderai davantage.

## 🔗 Documentation Complémentaire

Pour plus de détails, consultez :
- [Lien direct vers la section pertinente](URL) - [Description de ce que contient cette page]
- [Lien vers la page complète](URL) - [Description]
```

QUAND TU UTILISES LA BASE DE CONNAISSANCES:
- Analyse TOUS les résultats de recherche fournis en profondeur
- Combine les informations de plusieurs sources pour une réponse COMPLÈTE et ULTRA-DÉTAILLÉE
- **INCLUS TOUJOURS DES LIENS DIRECTS** vers les pages/sections pertinentes de l'aide en ligne
- **UTILISE LES CAPTURES D'ÉCRAN INTELLIGEMMENT** (maximum 2-3 images, SEULEMENT si pertinentes) :
  * **Place les images au bon endroit** : Insère-les dans la section pertinente de ta réponse, pas à la fin
  * **Référence explicitement** : "Dans l'image ci-dessous, vous pouvez voir [description TRÈS précise de chaque élément visible]"
  * **Guide visuellement** : "Cliquez sur le bouton visible dans l'image (en haut à droite, marqué 'Enregistrer', avec une icône de disquette)"
  * **Explique le contexte** : Décris ce que montre l'image et pourquoi c'est important pour résoudre le problème
  * **Intègre dans les étapes** : Si une image montre une étape spécifique, place-la juste avant ou après cette étape
  * **Décris TOUS les éléments visibles** : Nomme chaque bouton, champ, menu visible dans l'image
  * **Limite-toi à 2-3 images maximum** - choisis UNIQUEMENT les images qui montrent vraiment des fenêtres/logiciels, PAS des icônes
  * **Si aucune image pertinente** : Ne mentionne pas d'images, concentre-toi sur le texte explicatif ultra-détaillé

UTILISATION DES IMAGES POUR GUIDER (2-3 maximum):
1. **Orientation visuelle** : "Dans l'image 1, vous pouvez voir l'interface complète avec..."
2. **Instructions précises** : "Cliquez sur le bouton visible dans l'image 2 (en haut à droite, marqué 'Enregistrer')"
3. **Processus étape par étape** : "Suivez les images dans l'ordre : Image 1 montre l'état initial, Image 2 montre le résultat final"

LIENS VERS LA DOCUMENTATION (OBLIGATOIRE):
- **TOUJOURS inclure des liens cliquables** vers les pages/sections pertinentes de l'aide en ligne
- Utilise le format markdown : `[Titre de la section](URL)`
- Inclus les URLs complètes des documents sources dans chaque réponse
- Crée une section "🔗 Ressources et Documentation" avec tous les liens pertinents
- Les liens doivent mener directement à l'endroit pertinent dans l'aide en ligne

IMPORTANT (Support Client - Utilisateurs NON TECHNIQUES):
- Réponds en français sauf si l'utilisateur demande explicitement en anglais
- **Sois ULTRA-CLAIR et TRÈS ACCESSIBLE** - utilise un langage simple, évite TOUT jargon technique
- **Sois EXTRÊMEMENT COMPLET** - donne TOUTES les informations nécessaires, ne saute AUCUNE étape
- **Assume que l'utilisateur est un débutant** - explique TOUT, même les choses qui semblent évidentes
- **Sois empathique** - montre que tu comprends la frustration de l'utilisateur
- **Sois TRÈS actionnable** - chaque étape doit être si claire qu'un débutant peut la suivre sans hésitation
- **Décris TOUS les clics** : "Cliquez sur le menu 'Fichier' en haut à gauche" (pas juste "Allez dans Fichier")
- **Décris TOUS les chemins** : "Menu > Paramètres > Utilisateurs" avec explication de chaque niveau
- **Décris TOUS les champs** : Nom exact, emplacement, ce qu'il faut mettre dedans, comment le remplir
- **Indique ce qu'on devrait voir** : Après chaque action, dis ce que l'utilisateur devrait voir à l'écran
- Si tu n'es pas sûr, dis-le honnêtement et propose des pistes de vérification
- Pour les erreurs, fournis le contexte, les causes possibles, et les solutions étape par étape TRÈS détaillées
- Utilise TOUJOURS l'outil search_knowledge_base avant de répondre pour avoir des informations à jour
- **Place les images au bon endroit** : Intègre-les dans le texte pertinent, pas à la fin
- **Référence les images explicitement** : "Dans l'image ci-dessous, vous pouvez voir [description TRÈS précise]"
- **Guide visuellement** : Indique exactement où cliquer, quels champs remplir, en utilisant les images avec descriptions précises
- **Décris TOUS les éléments visibles dans les images** : Nomme chaque bouton, champ, menu visible
- **Maximum 2-3 images par réponse** - UNIQUEMENT si elles montrent des fenêtres/logiciels réels
- **Si les images ne sont pas pertinentes** : Ne les mentionne pas, concentre-toi sur le texte explicatif ultra-détaillé
- **TOUJOURS inclure des liens directs** vers les sections pertinentes de l'aide en ligne
- **Termine par une question** : Demande si le problème est résolu ou si l'utilisateur a besoin d'aide supplémentaire
- **Donne des exemples concrets** : Si applicable, donne des exemples de valeurs à entrer
- **Anticipe les problèmes** : Mentionne les erreurs courantes et comment les éviter"""
            
            model_auto = genai.GenerativeModel(
                model_name=params_model_name,
                tools=self.gemini_tools,
                system_instruction=system_instruction
            )
            chat_auto = model_auto.start_chat(history=history)
            
            # Send message and handle function calls manually
            response = chat_auto.send_message(last_content)
            
            # Handle function calls in a loop until we get a text response
            max_iterations = 10  # Prevent infinite loops
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # Check if response has function calls
                if hasattr(response, 'candidates') and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        parts = candidate.content.parts
                        
                        # Check if any part is a function call
                        function_call_part = None
                        for part in parts:
                            if hasattr(part, 'function_call') and part.function_call:
                                function_call_part = part
                                break
                        
                        if function_call_part:
                            function_call = function_call_part.function_call
                            function_name = function_call.name
                            
                            # Extract arguments
                            function_args = {}
                            if hasattr(function_call, 'args'):
                                # args is a Struct (protobuf), convert to dict
                                try:
                                    # Try MessageToDict first (works for most protobuf types)
                                    function_args = MessageToDict(function_call.args, preserving_proto_field_name=True)
                                except (AttributeError, TypeError) as e:
                                    # If that fails (e.g., MapComposite issue), try alternative methods
                                    try:
                                        # Method 1: Try dict() constructor if it's dict-like
                                        if isinstance(function_call.args, dict):
                                            function_args = function_call.args
                                        # Method 2: Try accessing as a mapping
                                        elif hasattr(function_call.args, 'keys'):
                                            function_args = {k: function_call.args[k] for k in function_call.args.keys()}
                                        # Method 3: Try __dict__ access
                                        elif hasattr(function_call.args, '__dict__'):
                                            function_args = {k: v for k, v in function_call.args.__dict__.items() 
                                                           if not k.startswith('_') and v is not None}
                                        # Method 4: Try direct attribute access for common fields
                                        else:
                                            # Try to get 'query' field directly
                                            if hasattr(function_call.args, 'query'):
                                                function_args['query'] = getattr(function_call.args, 'query')
                                            # Try other common field names
                                            for attr in ['text', 'input', 'message', 'prompt']:
                                                if hasattr(function_call.args, attr):
                                                    function_args['query'] = getattr(function_call.args, attr)
                                                    break
                                    except Exception as e2:
                                        # If all methods fail, log and use empty dict
                                        logger.warning(f"Could not extract function arguments: {e2}")
                                        function_args = {}
                            
                            # Execute the function
                            if function_name in self.tool_map:
                                # Handle query parameter
                                query = function_args.get('query', '')
                                function_result = self.tool_map[function_name](query)
                                
                                # Store images from search_kb for later inclusion
                                if function_name == "search_knowledge_base":
                                    # Extract images from the function result
                                    import re
                                    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
                                    extracted_images = re.findall(image_pattern, str(function_result))
                                    if extracted_images:
                                        # Store images to add to final response
                                        if not hasattr(self, '_extracted_images'):
                                            self._extracted_images = []
                                        self._extracted_images.extend(extracted_images)
                            else:
                                function_result = f"Unknown function: {function_name}"
                            
                            # Send function response back to Gemini
                            function_response = genai.protos.FunctionResponse(
                                name=function_name,
                                response={"result": str(function_result)}
                            )
                            response = chat_auto.send_message(
                                genai.protos.Part(function_response=function_response)
                            )
                            continue
                
                # No function call, return text response
                final_response = ""
                if hasattr(response, 'text'):
                    final_response = response.text
                elif hasattr(response, 'candidates') and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        if text_parts:
                            final_response = ''.join(text_parts)
                
                # Add extracted images to the response if they exist
                if final_response and hasattr(self, '_extracted_images') and self._extracted_images:
                    # Remove duplicates while preserving order and convert relative URLs to absolute
                    seen_images = set()
                    unique_images = []
                    base_url = 'https://aide.primlogix.com/prim/fr/5-8/'
                    
                    for alt, url in self._extracted_images:
                        # Convert relative URLs to absolute URLs
                        if url and not url.startswith('http'):
                            # Handle ./ prefix - urljoin doesn't work well with it
                            if url.startswith('./'):
                                url = url[2:]  # Remove ./ prefix
                            elif url.startswith('/'):
                                # Absolute path from domain root
                                base_url = 'https://aide.primlogix.com'
                            url = urljoin(base_url, url)
                            # Final check - ensure it's absolute
                            if not url.startswith('http'):
                                # Fallback: construct manually
                                if base_url.endswith('/'):
                                    url = base_url + url.lstrip('/')
                                else:
                                    url = base_url + '/' + url.lstrip('/')
                        
                        if url not in seen_images:
                            seen_images.add(url)
                            unique_images.append((alt, url))
                    
                    if unique_images:
                        # Add images section to response (limit to 2-3 maximum)
                        max_images_display = min(3, len(unique_images))
                        images_section = "\n\n---\n\n## 📸 Captures d'écran de l'interface\n\n"
                        for idx, (alt, url) in enumerate(unique_images[:max_images_display], 1):  # Limit to 3 images
                            alt_text = alt if alt and alt.strip() else f"Capture d'écran {idx}"
                            # Ensure URL is absolute
                            if not url.startswith('http'):
                                url = urljoin(base_url, url)
                            images_section += f"![{alt_text}]({url})\n\n"
                        final_response += images_section
                        # Clear extracted images for next query
                        self._extracted_images = []
                
                if final_response:
                    return final_response
                
                # If we get here, something unexpected happened
                break
            
            return "Error: Could not get a valid response from Gemini after multiple iterations."

        # Try common Gemini model names in order of preference
        # Remove -latest suffix if present, as it's not a valid model name format
        base_model_name = self.model_name.replace("-latest", "").strip()
        
        # Standard model names to try (in order of preference)
        # Updated to use Gemini 2.x models which are currently available
        model_names_to_try = [
            base_model_name,  # Try the user's model name first (without -latest)
            "gemini-2.5-flash",  # Latest and fastest
            "gemini-2.5-pro",   # Latest and most capable
            "gemini-2.0-flash", # Stable 2.0 version
            "gemini-2.0-flash-exp", # Experimental
            "gemini-pro",  # Fallback to older model
            "gemini-1.5-flash",
            "gemini-1.5-pro"
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        model_names_to_try = [m for m in model_names_to_try if m not in seen and not seen.add(m)]
        
        last_error = None
        last_model_tried = None
        for model_name_to_try in model_names_to_try:
            last_model_tried = model_name_to_try
            try:
                return attempt_chat(model_name_to_try)
            except Exception as e:
                last_error = e
                error_str = str(e)
                # Check if it's a model not found error
                is_model_error = ("404" in error_str or 
                                 "not found" in error_str.lower() or 
                                 "is not found" in error_str.lower() or
                                 "not supported" in error_str.lower())
                
                if not is_model_error:
                    # If it's not a model not found error, don't try other models
                    return f"Gemini Error: {last_error}"
                # Continue to next model if it's a model not found error
                continue
        
        # If we get here, all models failed - try to list available models
        try:
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    # Extract just the model name (remove 'models/' prefix if present)
                    model_name_clean = m.name.replace('models/', '')
                    available_models.append(model_name_clean)
            
            if available_models:
                available_models_str = ", ".join(available_models[:5])  # Show first 5
                return f"Gemini Error: Model '{last_model_tried}' not found. Last error: {last_error}. Available models: {available_models_str}. Please update the model name in the sidebar."
            else:
                return f"Gemini Error: Model '{last_model_tried}' not found. Last error: {last_error}. Please check your API key and try using 'gemini-1.5-flash', 'gemini-1.5-pro', or 'gemini-pro'."
        except Exception as list_error:
            return f"Gemini Error: Model '{last_model_tried}' not found. Last error: {last_error}. Could not list available models (error: {list_error}). Please check your API key and try using 'gemini-1.5-flash', 'gemini-1.5-pro', or 'gemini-pro'."

    def _run_ollama(self, messages):
        """Run agent with Ollama/LocalAI (OpenAI-compatible API)."""
        if not self.ollama_client:
            return "❌ Error: OpenAI client not available. Install with: pip install openai"
        
        # Convert messages to OpenAI format
        openai_messages = []
        for msg in messages:
            role = msg.get('role')
            content = msg.get('content', '')
            
            if role == 'user':
                openai_messages.append({"role": "user", "content": content})
            elif role == 'assistant':
                openai_messages.append({"role": "assistant", "content": content})
            elif role == 'tool':
                # Tool messages for function calling
                openai_messages.append({
                    "role": "tool",
                    "content": content,
                    "tool_call_id": msg.get('tool_call_id', '')
                })
        
        # Define tools for function calling
        tools = [{
            "type": "function",
            "function": {
                "name": "search_knowledge_base",
                "description": """Recherche approfondie dans la base de connaissances de la documentation PrimLogix.
                
UTILISE CET OUTIL pour:
- Trouver des solutions à des problèmes techniques ou erreurs
- Comprendre comment utiliser une fonctionnalité spécifique
- Obtenir des procédures détaillées étape par étape
- Trouver des exemples de configuration ou d'utilisation
- Rechercher des informations sur des champs, paramètres, ou options spécifiques

IMPORTANT:
- Utilise des termes techniques précis dans ta requête
- Combine les informations de plusieurs résultats pour donner une réponse complète
- Cite toujours les sources (URLs) dans ta réponse finale""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Requête de recherche détaillée et spécifique. Utilise des termes techniques précis, codes d'erreur, noms de fonctionnalités."
                        }
                    },
                    "required": ["query"]
                }
            }
        }]
        
        max_iterations = 10
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                # Call API with function calling
                response = self.ollama_client.chat.completions.create(
                    model=self.model_name,
                    messages=openai_messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.7,
                    max_tokens=2000
                )
                
                message = response.choices[0].message
                
                # Check for function calls
                if message.tool_calls:
                    # Add assistant message with tool calls
                    openai_messages.append({
                        "role": "assistant",
                        "content": message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in message.tool_calls
                        ]
                    })
                    
                    # Execute function calls
                    for tool_call in message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        if function_name in self.tool_map:
                            query = function_args.get('query', '')
                            function_result = self.tool_map[function_name](query)
                            
                            # Add tool result
                            openai_messages.append({
                                "role": "tool",
                                "content": str(function_result),
                                "tool_call_id": tool_call.id
                            })
                    
                    continue
                
                # Return text response
                if message.content:
                    return message.content
                else:
                    return "❌ No response content from model"
                    
            except Exception as e:
                logger.error(f"Ollama API error: {e}")
                return f"❌ Error calling Ollama API: {str(e)}\n\nMake sure Ollama is running: ollama serve\nAnd the model is installed: ollama pull {self.model_name}"
        
        return "❌ Error: Maximum iterations reached without getting a final response."
