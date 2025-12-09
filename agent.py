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
            
            # Search with more results for better coverage and context
            results = query_knowledge_base(query, n_results=10)
            
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
            
            # Build detailed context with relevance scores
            context_parts = []
            all_images = []  # Collect all images from results
            seen_urls = set()  # Track unique URLs to avoid duplicates
            
            context_parts.append(f"📚 **Résultats de recherche** (requête: \"{query}\")\n")
            context_parts.append(f"Trouvé {len(docs)} document(s) pertinent(s) dans la base de connaissances PrimLogix:\n")
            
            for i, doc in enumerate(docs):
                if not doc or not doc.strip():
                    continue
                    
                source = metadatas[i].get('url', 'URL inconnue') if i < len(metadatas) else 'URL inconnue'
                title = metadatas[i].get('title', 'Sans titre') if i < len(metadatas) else 'Sans titre'
                chunk_idx = metadatas[i].get('chunk_index', '?') if i < len(metadatas) else '?'
                
                # Calculate relevance score
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
                    else:
                        relevance_badge = "⚪ [Peu pertinent]"
                    relevance_badge += f" (Score: {relevance_score}%)"
                
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
                                img_with_context['document_url'] = source
                                img_with_context['relevance_score'] = relevance_score
                                img_with_context['url'] = img_url  # Ensure absolute URL
                                all_images.append(img_with_context)
                    except Exception as e:
                        logger.debug(f"Error parsing images: {e}")
                        pass
                
                # Build detailed source info
                source_info = f"\n### 📄 Document #{i+1}: {title}"
                if relevance_badge:
                    source_info += f" {relevance_badge}"
                source_info += f"\n**URL:** {source}"
                source_info += f"\n**Chunk:** {chunk_idx}"
                source_info += f"\n\n**Contenu:**\n{doc}\n"
                source_info += "\n" + "─" * 60 + "\n"
                
                context_parts.append(source_info)
            
            if not context_parts:
                return "❌ Aucune documentation pertinente trouvée dans la base de connaissances PrimLogix."
            
            # Combine all context
            response_text = "\n".join(context_parts)
            
            # Add summary statistics
            response_text += f"\n\n**📊 Résumé:** {len(docs)} document(s) trouvé(s)"
            if all_images:
                response_text += f", {len(all_images)} image(s) associée(s)"
            
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
                    
                    # Additional filtering: ensure it's a real screenshot, not an icon/logo
                    img_url = img.get('url', '').lower()
                    img_description = (img.get('description', '') + ' ' + img.get('alt', '') + ' ' + img.get('title', '')).lower()
                    
                    # Check dimensions if available
                    img_width = img.get('width')
                    img_height = img.get('height')
                    if img_width and img_width < 100:
                        continue  # Too small, likely an icon
                    if img_height and img_height < 100:
                        continue  # Too small, likely an icon
                    
                    # Exclude common icon/logo patterns in filename
                    icon_patterns = ['icon', 'logo', 'button', 'arrow', 'chevron', 'nav', 'menu', 
                                    '40x40', '32x32', '24x24', '16x16', '20x20', 'favicon', 'sprite']
                    if any(pattern in img_url for pattern in icon_patterns):
                        # But allow if it's clearly a screenshot
                        if not any(x in img_url for x in ['screenshot', 'capture', 'interface', 'fenetre', 'ecran']):
                            continue
                    
                    # Must have screenshot-related keywords in URL or description
                    screenshot_keywords = ['screenshot', 'capture', 'interface', 'fenetre', 'ecran', 
                                         'affichage', 'window', 'dialog', 'images/']
                    if not any(keyword in img_url or keyword in img_description for keyword in screenshot_keywords):
                        continue
                    
                    # Include this image - it's relevant and looks like a real screenshot
                    relevant_images.append(img)
                
                # Sort by relevance score (highest first), then by document order
                relevant_images.sort(key=lambda x: (
                    x.get('relevance_score', 0) if x.get('relevance_score') is not None else 0
                ), reverse=True)
                
                # Limit to top 8 most relevant images to avoid overwhelming the response
                # This ensures images complement the answer without being excessive
                top_images = relevant_images[:8]
                
                if top_images:
                    # Add descriptive section header with instructions for the agent
                    image_section = "\n\n---\n\n## 📸 Captures d'écran pertinentes de l'interface PrimLogix\n\n"
                    image_section += f"*{len(top_images)} capture(s) d'écran pertinente(s) extraite(s) de la documentation officielle*\n\n"
                    image_section += "**IMPORTANT pour l'agent:** Ces images proviennent directement de l'aide en ligne PrimLogix et complètent la réponse. Utilise-les pour guider l'utilisateur visuellement. Référence-les explicitement dans ta réponse (ex: 'Comme on peut le voir dans l'image 1...') et explique ce qu'elles montrent.\n\n"
                    
                    for idx, img in enumerate(top_images, 1):  # Top 8 most relevant images
                        # Build comprehensive description
                        description_parts = []
                        
                        # Build comprehensive description with priority order:
                        # 1. Context (most relevant to query)
                        # 2. Description (enhanced description from scraper)
                        # 3. Alt/Title (basic image info)
                        # 4. Document info and relevance
                        
                        # Start with context if available (most relevant to the query)
                        if img.get('context'):
                            context = img.get('context', '')[:150]  # Limit context length
                            if context:
                                description_parts.append(f"Contexte: {context}")
                        
                        # Add enhanced description from scraper (includes alt, title, caption, context)
                        if img.get('description'):
                            description_parts.append(img['description'])
                        elif img.get('alt'):
                            description_parts.append(img['alt'])
                        elif img.get('title'):
                            description_parts.append(img['title'])
                        
                        # Add caption if available (figure captions are very descriptive)
                        if img.get('caption'):
                            description_parts.append(f"Légende: {img['caption']}")
                        
                        # Add document source for traceability
                        if img.get('document_title'):
                            description_parts.append(f"Source: {img['document_title']}")
                        
                        # Add relevance score to help agent prioritize
                        relevance_score = img.get('relevance_score')
                        if relevance_score is not None:
                            if relevance_score >= 80:
                                relevance_label = "Très pertinent"
                            elif relevance_score >= 60:
                                relevance_label = "Pertinent"
                            elif relevance_score >= 40:
                                relevance_label = "Modérément pertinent"
                            else:
                                relevance_label = "Peu pertinent"
                            description_parts.append(f"Pertinence: {relevance_label}")
                        
                        # Combine into final description
                        alt_text = " | ".join(description_parts) if description_parts else f'Capture d\'écran {idx} de l\'interface PrimLogix'
                        
                        # Clean alt text for better display
                        alt_text = alt_text.replace('\n', ' ').strip()[:150]  # Increased to 150 chars
                        if not alt_text:
                            alt_text = f"Capture d'écran {idx} de l'interface PrimLogix"
                        
                        # Add image with enhanced description
                        # Ensure absolute URL - convert relative URLs to absolute
                        # CRITICAL: Always get fresh URL from dict and convert if needed
                        img_url = img.get('url', '')
                        
                        # Force conversion to absolute URL
                        if not img_url.startswith('http'):
                            # Convert relative URL to absolute using document URL
                            base_url = img.get('document_url', 'https://aide.primlogix.com/prim/fr/5-8/')
                            if not base_url.startswith('http'):
                                base_url = 'https://aide.primlogix.com/prim/fr/5-8/'
                            
                            # Handle ./ prefix - urljoin doesn't work well with it
                            if img_url.startswith('./'):
                                img_url = img_url[2:]  # Remove ./ prefix
                            elif img_url.startswith('/'):
                                # Absolute path from domain root
                                base_url = 'https://aide.primlogix.com'
                            
                            # Use urljoin
                            img_url = urljoin(base_url, img_url)
                            
                            # Final check - ensure it's absolute (should always be after urljoin, but double-check)
                            if not img_url.startswith('http'):
                                # Fallback: construct manually
                                if base_url.endswith('/'):
                                    img_url = base_url + img_url.lstrip('/')
                                else:
                                    img_url = base_url + '/' + img_url.lstrip('/')
                            
                            # Update in dict for consistency
                            img['url'] = img_url
                        
                        # Final safety check before adding to markdown
                        if not img_url.startswith('http'):
                            # Last resort: use base URL
                            img_url = 'https://aide.primlogix.com/prim/fr/5-8/' + img_url.lstrip('./')
                        
                        image_section += f"### Image {idx}\n\n"
                        image_section += f"![{alt_text}]({img_url})\n\n"
                        
                        # Add detailed caption with all available information
                        caption_parts = []
                        if img.get('description') and img['description'] != alt_text:
                            caption_parts.append(f"**Description:** {img['description']}")
                        if img.get('context'):
                            caption_parts.append(f"**Contexte:** {img['context'][:100]}...")
                        if img.get('document_title'):
                            caption_parts.append(f"**Source:** {img['document_title']}")
                        
                        if caption_parts:
                            image_section += "*" + " | ".join(caption_parts) + "*\n\n"
                        image_section += "---\n\n"
                    
                    response_text += image_section
            
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
            # Enhanced system instruction for detailed, debugging-friendly responses
            system_instruction = """Tu es PRIMBOT, un assistant expert spécialisé dans l'aide au débogage et la résolution de problèmes pour PrimLogix.

TON RÔLE:
- Aider les utilisateurs à résoudre des problèmes techniques avec PrimLogix
- Fournir des réponses DÉTAILLÉES et STRUCTURÉES pour faciliter le débogage
- Expliquer les étapes de résolution de manière claire et méthodique
- Citer les sources de documentation utilisées

STYLE DE RÉPONSE:
1. **Structure claire**: Utilise des titres, listes à puces, et sections bien organisées
2. **Détails techniques**: Inclus les informations spécifiques (noms de champs, valeurs, chemins, etc.)
3. **Étapes numérotées**: Pour les procédures, utilise des étapes numérotées
4. **Citations**: Mentionne toujours les sources de documentation utilisées
5. **Exemples concrets**: Fournis des exemples de code, configurations, ou valeurs si pertinent
6. **Diagnostic**: Si le problème n'est pas clair, propose des étapes de diagnostic

QUAND TU UTILISES LA BASE DE CONNAISSANCES:
- Analyse TOUS les résultats de recherche fournis
- Combine les informations de plusieurs sources si nécessaire
- Mentionne les scores de pertinence si disponibles
- **UTILISE LES CAPTURES D'ÉCRAN POUR GUIDER L'UTILISATEUR** :
  * Référence explicitement les images dans ta réponse (ex: "Comme on peut le voir dans l'image 1...")
  * Décris ce que montre chaque image en détail
  * Utilise les images pour donner des instructions étape par étape
  * Indique où cliquer, quels champs remplir, quels menus ouvrir
  * Guide visuellement l'utilisateur en pointant vers les éléments de l'interface visibles dans les images
  * Si plusieurs images sont disponibles, utilise-les pour montrer un processus complet
  * Mentionne les numéros d'images pour que l'utilisateur puisse les suivre

UTILISATION DES IMAGES POUR GUIDER:
1. **Orientation visuelle** : "Dans l'image 1, vous pouvez voir..."
2. **Instructions précises** : "Cliquez sur le bouton visible dans l'image 2 (en haut à droite)"
3. **Processus étape par étape** : "Suivez les images dans l'ordre : Image 1 → Image 2 → Image 3"
4. **Détection d'éléments** : "Dans l'image, repérez le champ 'Nom' (visible au centre)"
5. **Navigation** : "Utilisez le menu visible dans l'image pour accéder à..."

IMPORTANT:
- Réponds en français sauf si l'utilisateur demande explicitement en anglais
- Sois précis et technique, mais reste accessible
- Si tu n'es pas sûr, dis-le et propose des pistes de vérification
- Pour les erreurs, fournis toujours le contexte et les causes possibles
- Utilise TOUJOURS l'outil search_knowledge_base avant de répondre pour avoir des informations à jour
- **TOUJOURS référencer les images par leur numéro** (Image 1, Image 2, etc.) quand tu guides l'utilisateur
- **Décris visuellement** ce que l'utilisateur doit voir et faire en utilisant les images comme référence"""
            
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
                        # Add images section to response
                        images_section = "\n\n---\n\n## 📸 Captures d'écran de l'interface\n\n"
                        for idx, (alt, url) in enumerate(unique_images[:12], 1):  # Limit to 12 images
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
