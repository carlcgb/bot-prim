# Suppress warnings BEFORE any imports
import warnings
import os
warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', message='.*duckduckgo_search.*')
# Suppress Google ALTS warnings BEFORE importing google.generativeai
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '3'  # 3 = FATAL only (more aggressive)
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['GRPC_PYTHON_LOGLEVEL'] = 'ERROR'

# Import DDGS with warnings suppressed
with warnings.catch_warnings():
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    warnings.filterwarnings('ignore', message='.*duckduckgo_search.*')
    try:
        from ddgs import DDGS
    except ImportError:
        # Fallback for old package name
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            DDGS = None
from knowledge_base import query_knowledge_base
import json
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

class PrimAgent:
    def __init__(self, api_key, base_url=None, model="gemini-2.5-flash", provider="Google Gemini"):
        # Gemini is now mandatory
        if provider != "Google Gemini":
            raise ValueError("Only Google Gemini is supported. Please use provider='Google Gemini'")
        
        self.provider = "Google Gemini"
        self.model_name = model
        # Suppress warnings when initializing DDGS
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=RuntimeWarning)
            if DDGS is None:
                raise ImportError("ddgs package is required. Install it with: pip install ddgs")
            self.ddgs = DDGS()
        
        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # Define Gemini Tools using FunctionDeclaration
        self.gemini_tools = [
            genai.protos.Tool(
                function_declarations=[
                    genai.protos.FunctionDeclaration(
                        name="search_knowledge_base",
                        description="Search the PrimLogix technical documentation for debugging client issues. Use this for: PrimLogix-specific errors, field configurations, database issues, API problems, feature implementation details, configuration parameters, and technical procedures. IMPORTANT: If the first search doesn't return enough results, try multiple searches with different query terms (synonyms, related terms, broader/narrower terms) to find all relevant information.",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "query": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="Technical search query. Include: error codes, field names, feature names, configuration paths, database references, or specific technical terms from PrimLogix. Try multiple variations if first search doesn't find enough information."
                                )
                            },
                            required=["query"]
                        )
                    ),
                        genai.protos.FunctionDeclaration(
                            name="search_internet",
                            description="Search the internet for technical information to COMPLEMENT PrimLogix documentation. Use this for: SMTP/IMAP/POP port numbers, server addresses, email provider configurations (Outlook, Gmail, etc.), general technical standards, network troubleshooting, or any technical details that might not be in the PrimLogix documentation. ALWAYS use search_knowledge_base FIRST for PrimLogix-specific steps and procedures, then use search_internet to find missing technical details (ports, servers, configuration values).",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "query": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="Technical search query for specific information needed: port numbers, server addresses, email provider settings, technical standards, or configuration values. Examples: 'SMTP port Outlook 365', 'Gmail IMAP settings', 'POP3 port number'."
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
            "search_knowledge_base": self._search_kb,
            "search_internet": self._search_web
        }


    def _expand_query(self, query):
        """Expand query with synonyms and variations for better understanding."""
        query_lower = query.lower()
        expanded = [query]  # Always include original
        
        # Common PrimLogix terms and synonyms
        synonyms = {
            'edit': ['modifier', 'changer', 'éditer', 'configurer'],
            'create': ['créer', 'ajouter', 'nouveau', 'faire'],
            'delete': ['supprimer', 'retirer', 'enlever'],
            'configure': ['configurer', 'paramétrer', 'configuration'],
            'protocol': ['protocole'],
            'email': ['courriel', 'courrier', 'e-mail'],
            'smtp': ['smtp', 'envoi'],
            'imap': ['imap', 'réception'],
            'pop': ['pop', 'pop3'],
            'user': ['utilisateur', 'usager', 'user'],
            'candidate': ['candidat', 'candidats', 'utilisateur', 'user'],
            'password': ['mot de passe', 'mdp'],
            'profile': ['profil'],
            'settings': ['paramètres', 'configuration'],
            'menu': ['menu', 'navigation'],
            'where': ['où', 'comment accéder', 'comment aller'],
            'how': ['comment', 'procédure', 'étapes', 'faire']
        }
        
        # Special handling for candidate/user creation queries
        if any(term in query_lower for term in ['candidat', 'candidate', 'utilisateur', 'user']):
            if any(term in query_lower for term in ['créer', 'create', 'ajouter', 'nouveau', 'faire']):
                # Add specific document search terms for user/candidate creation
                expanded.append('dlg103')
                expanded.append('dlg103.html')
                expanded.append('créer utilisateur affecter groupe')
                expanded.append('nouveau utilisateur')
                expanded.append('ajouter utilisateur')
        
        # Check for document IDs (like dlg103) in query
        import re
        doc_id_pattern = r'\bdlg\d+\b'
        doc_ids = re.findall(doc_id_pattern, query_lower)
        if doc_ids:
            # Add document ID variations
            for doc_id in doc_ids:
                expanded.append(doc_id)  # Keep original format
                expanded.append(doc_id.upper())  # Uppercase version
                # Add with .html extension
                expanded.append(f"{doc_id}.html")
                expanded.append(f"{doc_id.upper()}.html")
        
        # Add PrimLogix context if not present
        if 'primlogix' not in query_lower:
            expanded.append(query + " PrimLogix")
        
        # Add lowercase version
        if query != query.lower():
            expanded.append(query.lower())
        
        # Add variations with common synonyms
        for key, values in synonyms.items():
            if key in query_lower:
                for synonym in values:
                    if synonym not in query_lower:
                        expanded.append(query.replace(key, synonym))
        
        # Configuration/config variations
        if "configuration" in query_lower:
            expanded.append(query.replace("configuration", "config"))
        elif "config" in query_lower and "configuration" not in query_lower:
            expanded.append(query.replace("config", "configuration"))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_expanded = []
        for q in expanded:
            if q.lower() not in seen:
                seen.add(q.lower())
                unique_expanded.append(q)
        
        return unique_expanded[:8]  # Limit to 8 variations (increased for better coverage)
    
    def _search_kb(self, query):
        try:
            # Expand query for better understanding
            search_queries = self._expand_query(query)
            
            # Search with more results initially to filter later
            all_results = []
            
            # Collect results from multiple queries (increased to 4 for better coverage)
            seen_ids = set()
            # Prioritize original query, then try variations
            for search_query in search_queries[:4]:  # Increased to 4 queries for better coverage
                try:
                    query_results = query_knowledge_base(search_query, n_results=8)  # Reduced for speed
                    if query_results and query_results.get('documents') and query_results['documents'][0]:
                        docs = query_results['documents'][0]
                        metadatas = query_results['metadatas'][0]
                        distances = query_results.get('distances', [None])[0] if query_results.get('distances') else [None] * len(docs)
                        
                        for i, doc in enumerate(docs):
                            if not doc or not doc.strip():
                                continue
                            
                            # Calculate relevance score
                            distance = distances[i] if i < len(distances) and distances[i] is not None else 1.0
                            score = max(0, min(100, int((1 - distance) * 100)))
                            
                            # Create unique ID from URL + chunk
                            source = metadatas[i].get('url', '') if i < len(metadatas) else ''
                            chunk_idx = metadatas[i].get('chunk_index', i) if i < len(metadatas) else i
                            doc_id = f"{source}_{chunk_idx}"
                            
                            # Skip duplicates
                            if doc_id in seen_ids:
                                continue
                            seen_ids.add(doc_id)
                            
                            # Extract images from metadata
                            images = []
                            metadata_obj = metadatas[i] if i < len(metadatas) else {}
                            if metadata_obj:
                                images_json = metadata_obj.get('images', '')
                                if images_json:
                                    try:
                                        import json
                                        images = json.loads(images_json) if isinstance(images_json, str) else images_json
                                    except (json.JSONDecodeError, TypeError):
                                        images = []
                            
                            all_results.append({
                                'doc': doc,
                                'metadata': metadata_obj,
                                'score': score,
                                'distance': distance,
                                'images': images  # Store images with result
                            })
                except Exception as e:
                    logger.warning(f"Error with query '{search_query}': {e}")
                    continue
            
            if not all_results:
                return f"Aucune documentation pertinente trouvée pour '{query}'. Essayez avec des termes différents ou vérifiez si l'information existe dans la base de connaissances."
            
            # Sort by relevance score (highest first)
            all_results.sort(key=lambda x: x['score'], reverse=True)
            
            # Filter by minimum relevance threshold (25% - lowered further to catch more relevant docs)
            filtered_results = [r for r in all_results if r['score'] >= 25]
            
            # If we have good results (score >= 50%), prioritize them
            high_relevance = [r for r in filtered_results if r['score'] >= 50]
            if len(high_relevance) >= 3:
                filtered_results = high_relevance[:10]  # Top 10 high-relevance results
            else:
                # Mix of high and medium relevance, but limit total
                filtered_results = filtered_results[:10]  # Top 10 results
            
            if not filtered_results:
                # If no results above 25%, use top 8 even if lower
                # This ensures we always have some context
                filtered_results = all_results[:8]
            
            # Build context with filtered and sorted results
            context = f"📚 Résultats de recherche dans la documentation PrimLogix pour: '{query}'\n"
            context += f"Trouvé {len(filtered_results)} document(s) pertinent(s) (filtrés par pertinence ≥25%)\n\n"
            context += "**⚠️ IMPORTANT : Utilise UNIQUEMENT les informations des documents ci-dessous. Les documents sont triés par pertinence (score le plus élevé en premier). Privilégie les documents avec score 🟢 (≥70%) ou 🟡 (≥50%), mais UTILISE AUSSI les documents avec score 🟠 (≥25%) - ils contiennent probablement l'information recherchée.**\n\n"
            
            seen_docs = set()  # Avoid exact duplicate content
            all_images = []  # Collect all relevant images
            
            for idx, result in enumerate(filtered_results, 1):
                doc = result['doc']
                metadata = result['metadata']
                score = result['score']
                images = result.get('images', [])
                
                # Skip exact duplicate content
                doc_hash = hash(doc[:200])  # Use first 200 chars for better duplicate detection
                if doc_hash in seen_docs:
                    continue
                seen_docs.add(doc_hash)
                
                source = metadata.get('url', 'URL unknown')
                title = metadata.get('title', 'Untitled')
                chunk_idx = metadata.get('chunk_index', '?')
                
                # Relevance score indicator
                if score >= 70:
                    relevance_score = f" [🟢 {score}% - TRÈS PERTINENT]"
                elif score >= 50:
                    relevance_score = f" [🟡 {score}% - PERTINENT]"
                elif score >= 40:
                    relevance_score = f" [🟠 {score}% - MODÉRÉMENT PERTINENT]"
                else:
                    relevance_score = f" [⚪ {score}%]"
                
                # Optimized content length - more for high relevance
                max_length = 6000 if score >= 70 else 4000 if score >= 50 else 3000
                doc_content = doc[:max_length] if len(doc) > max_length else doc
                if len(doc) > max_length:
                    doc_content += "\n[... contenu tronqué ...]"
                
                context += f"### Document #{idx}: {title}{relevance_score}\n"
                context += f"**URL:** {source}\n"
                context += f"**Chunk:** {chunk_idx}\n"
                context += f"**⚠️ IMPORTANT:** Si tu utilises les informations de ce document dans ta réponse, TU DOIS inclure cette URL exacte ({source}) dans la section documentation de ta réponse, et l'associer au contenu spécifique de ce document que tu utilises.\n"
                
                # Add images if available - PRIORITIZE full interface screenshots over emojis/icons
                if images:
                    # Filter and score images - prioritize large rectangular screenshots
                    scored_images = []
                    for img in images:
                        img_url = img.get('url', '') if isinstance(img, dict) else str(img)
                        img_alt = img.get('alt', '') if isinstance(img, dict) else ''
                        img_context = img.get('context', '') if isinstance(img, dict) else ''
                        img_width = img.get('width') if isinstance(img, dict) else None
                        img_height = img.get('height') if isinstance(img, dict) else None
                        
                        # Only include images from aide.primlogix.com (the official help site)
                        if img_url and 'aide.primlogix.com' in img_url:
                            img_lower = (img_url + ' ' + img_alt + ' ' + img_context).lower()
                            
                            # STRICT: Exclude emojis, icons, and small graphics
                            emoji_icon_patterns = [
                                'emoji', 'emoticon', 'smiley', 'smile', '😀', '😊', '👍', '👎',
                                'icon', 'icone', 'icône', 'logo', 'button', 'bouton',
                                'arrow', 'fleche', 'flèche', 'chevron', 'nav', 'menu',
                                'stop', 'stop-sign', 'warning', 'avertissement', 'alert',
                                'checkmark', 'check', 'tick', 'coche', 'verification',
                                'person', 'user', 'utilisateur', 'silhouette', 'avatar',
                                'document', 'folder', 'file', 'dossier', 'cv',
                                'favicon', '.ico', 'svg', 'sprite', 'glyph'
                            ]
                            if any(pattern in img_lower for pattern in emoji_icon_patterns):
                                # Only allow if explicitly marked as screenshot/interface
                                if not any(x in img_lower for x in ['screenshot', 'capture', 'interface', 'fenetre', 'ecran', 'affichage', 'window', 'dialog', 'images/']):
                                    continue  # Skip emojis/icons
                            
                            # Exclude small square icons
                            is_small_icon = False
                            small_icon_sizes = ['16x16', '20x20', '24x24', '32x32', '40x40', '48x48', '50x50', '56x56', '60x60', '63x63', '64x64', '72x72', '80x80', '96x96', '100x100', '128x128']
                            if any(size in img_url.lower() for size in small_icon_sizes):
                                if '/images/' not in img_url.lower() and '/img/' not in img_url.lower():
                                    continue  # Skip small icons
                            
                            # Calculate priority score (higher = better, prioritize full interface screenshots)
                            priority_score = 0
                            
                            # HIGH PRIORITY: Large rectangular images (full interface screenshots)
                            width_val = None
                            height_val = None
                            try:
                                if img_width and isinstance(img_width, (int, str)):
                                    width_val = int(img_width) if str(img_width).isdigit() else None
                                if img_height and isinstance(img_height, (int, str)):
                                    height_val = int(img_height) if str(img_height).isdigit() else None
                            except (ValueError, TypeError):
                                pass
                            
                            if width_val and height_val and width_val > 0 and height_val > 0:
                                # Large images (likely full screenshots)
                                if width_val >= 600 or height_val >= 400:
                                    priority_score += 50
                                elif width_val >= 400 or height_val >= 300:
                                    priority_score += 30
                                
                                # Rectangular images (screenshots are usually rectangular, not square)
                                ratio = max(width_val, height_val) / min(width_val, height_val)
                                if ratio > 1.5:  # Significantly rectangular
                                    priority_score += 20
                                elif ratio > 1.2:  # Moderately rectangular
                                    priority_score += 10
                                elif ratio < 1.1:  # Square or near-square (likely icon)
                                    priority_score -= 30  # Penalize square images
                            
                            # HIGH PRIORITY: Images in /images/ directory (where screenshots are stored)
                            if '/images/' in img_url.lower():
                                priority_score += 40
                            
                            # HIGH PRIORITY: Explicit screenshot keywords
                            screenshot_keywords = ['screenshot', 'capture', 'interface', 'fenetre', 'ecran', 'affichage', 'window', 'dialog', 'application', 'logiciel']
                            if any(keyword in img_lower for keyword in screenshot_keywords):
                                priority_score += 30
                            
                            # MEDIUM PRIORITY: PNG/JPG/JPEG (not SVG/GIF which are often icons)
                            if any(img_url.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
                                priority_score += 10
                            
                            # LOW PRIORITY: Small images or square images
                            if width_val and height_val:
                                if width_val < 200 or height_val < 200:
                                    priority_score -= 20
                            
                            # Only include images with positive priority score (prioritize screenshots)
                            if priority_score > 0:
                                scored_images.append({
                                    'url': img_url,
                                    'alt': img_alt or 'Capture d\'écran PrimLogix',
                                    'context': img_context,
                                    'score': priority_score,
                                    'width': width_val,
                                    'height': height_val
                                })
                    
                    # Sort by priority score (highest first) to prioritize full interface screenshots
                    scored_images.sort(key=lambda x: x['score'], reverse=True)
                    
                    # Add images to context (limit to 5 per document, prioritizing highest scores)
                    if scored_images:
                        context += f"\n**📸 Images de l'aide en ligne PrimLogix (⚠️ TU DOIS INCLURE CES IMAGES DANS TA RÉPONSE - NE DIS JAMAIS QUE TU NE PEUX PAS AFFICHER D'IMAGES) :**\n"
                        for img_idx, img in enumerate(scored_images[:5], 1):  # Top 5 highest priority images
                            img_url = img['url']
                            img_alt = img.get('alt', 'Capture d\'écran PrimLogix')
                            img_context = img.get('context', '')
                            
                            # Add image markdown with clear instruction
                            context += f"**Image {img_idx}:** ![{img_alt}]({img_url})\n"
                            if img_context:
                                context += f"*Contexte: {img_context[:150]}...*\n"
                            context += f"*⚠️ IMPORTANT: Tu DOIS inclure cette image dans ta réponse avec le format markdown exact: `![{img_alt}]({img_url})`*\n\n"
                            
                            # Also collect for final images section
                            all_images.append({
                                'url': img_url,
                                'alt': img_alt,
                                'context': img_context,
                                'title': title,
                                'score': score
                            })
                        context += "\n"
                
                context += f"**Contenu technique:**\n{doc_content}\n"
                context += "---\n\n"
            
            # Add direct links section (simplified for speed)
            context += "\n**🔗 URLs des documents (utilise les URLs des documents que tu utilises):**\n"
            seen_urls = set()
            for result in filtered_results[:3]:  # Top 3 URLs only for speed
                metadata = result['metadata']
                source = metadata.get('url', '')
                title = metadata.get('title', 'Untitled')
                if source and source not in seen_urls:
                    seen_urls.add(source)
                    context += f"- [{title}]({source})\n"
            
            # Add images section at the end (top 5 most relevant images)
            if all_images:
                # Sort by relevance score and get top 5
                all_images.sort(key=lambda x: x.get('score', 0), reverse=True)
                top_images = all_images[:5]
                
                context += "\n**📸 Images pertinentes de l'aide en ligne PrimLogix:**\n"
                for img in top_images:
                    context += f"![{img['alt']}]({img['url']})\n"
                    if img.get('context'):
                        context += f"*{img['context'][:150]}...*\n"
                    context += f"*Source: {img['title']}*\n\n"
            
            return context
        except Exception as e:
            logger.error(f"Error searching KB: {e}", exc_info=True)
            return f"Erreur lors de la recherche dans la base de connaissances: {e}"

    def _search_web(self, query):
        print(f"DEBUG: Searching Web for '{query}'")
        try:
            # Search with more results for better coverage
            results = self.ddgs.text(query, max_results=5)
            if not results:
                return f"No internet results found for '{query}'. Try different search terms."
            
            context = f"🌐 Internet Search Results for: '{query}'\n"
            context += f"Found {len(results)} result(s)\n\n"
            
            for i, r in enumerate(results, 1):
                context += f"### Result #{i}: {r.get('title', 'Untitled')}\n"
                context += f"**Link:** {r.get('href', 'N/A')}\n"
                context += f"**Snippet:** {r.get('body', 'No description available')}\n"
                context += "---\n\n"
            
            return context
        except Exception as e:
            logger.error(f"Error searching internet: {e}", exc_info=True)
            return f"Error searching internet: {e}"

    def run(self, messages):
        # Only Gemini is supported
        return self._run_gemini(messages)
        # Technical system instruction for debugging-oriented responses
        system_message = {
            "role": "system",
            "content": """You are PRIMBOT, a technical debugging assistant for PrimLogix software. Your role is to help developers and technical support staff debug client issues efficiently.

TECHNICAL ORIENTATION:
- Provide technical, concise, and actionable debugging information
- Focus on root causes, error codes, configuration issues, and technical solutions
- Use technical terminology (field names, error codes, API endpoints, database queries)
- Include specific technical details: field IDs, table names, configuration paths, log patterns
- Prioritize diagnostic steps and troubleshooting procedures

RESPONSE STRUCTURE:
1. **Quick Diagnosis**: Immediate technical assessment of the issue
2. **Root Cause Analysis**: Technical explanation of why the issue occurs
3. **Technical Solution**: Step-by-step technical fix with specific details
4. **Verification Steps**: Technical checks to confirm resolution
5. **Related Issues**: Common related technical problems and solutions

TECHNICAL DETAILS TO INCLUDE:
- Exact field names, IDs, and database references
- Error codes and their meanings
- Configuration file paths and parameter names
- API endpoints and request/response formats
- Database table/column names when relevant
- Log file locations and what to look for
- Network/connection troubleshooting steps

TOOLS USAGE:
- ALWAYS search the knowledge base FIRST for PrimLogix-related questions - try multiple search queries with different terms if first search doesn't find enough information
- If knowledge base search returns few or no results, try alternative search terms (synonyms, related terms, broader/narrower terms)
- Use search_internet for general technical issues (email config, SMTP, network issues, etc.) OR when knowledge base doesn't have the information
- If initial search finds limited information, perform additional searches with related terms to get comprehensive coverage
- Combine multiple search results from both knowledge base and internet for comprehensive technical answers
- Don't give up after one search - be thorough and search multiple times with different query variations

RESPONSE STYLE:
- Be direct and technical - no unnecessary explanations
- Use code blocks for configuration examples, SQL queries, or command-line instructions
- Include specific values, paths, and technical references
- Provide multiple solution approaches when applicable
- Reference documentation URLs for detailed technical information

LANGUAGE:
- Respond in French unless the user asks in English
- Use technical French terminology from PrimLogix documentation"""
        }
        
        # Prepend system message if not already present
        if messages and messages[0].get("role") != "system":
            messages = [system_message] + messages
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=self.openai_tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        if message.tool_calls:
            messages.append(message)
            
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                result_content = ""
                if function_name == "search_knowledge_base":
                    result_content = self._search_kb(arguments['query'])
                elif function_name == "search_internet":
                    result_content = self._search_web(arguments['query'])
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": result_content
                })
            
            final_response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return final_response.choices[0].message.content
        
        return message.content

    def _run_gemini(self, messages):
        # Convert OpenAI messages to Gemini History
        history = []
        for msg in messages[:-1]: # All but last
            role = msg['role']
            content = msg.get('content')
            if role == 'user':
                history.append({'role': 'user', 'parts': [content]})
            elif role == 'assistant':
                history.append({'role': 'model', 'parts': [content]})
        
        last_msg = messages[-1]
        last_content = last_msg['content']
        
        def attempt_chat(params_model_name):
            # Compact but complete system instruction - PRIMLOGIX ONLY
            system_instruction = """Tu es PRIMBOT, assistant expert PrimLogix. Fournis des réponses COMPACTES mais COMPLÈTES, spécifiques à PrimLogix uniquement.

⚠️ RÈGLES ABSOLUES :
- **TOUJOURS répondre** - même si tu as déjà répondu à une question similaire, fournis une réponse complète et fraîche
- **Réponses SPÉCIFIQUES PrimLogix** - utilise les noms EXACTS de menus/boutons/champs de PrimLogix
- **Format COMPACT** - sois concis mais complet, évite la répétition inutile
- **Étapes numérotées** : TOUJOURS commencer par "### Étape 1:" et numéroter séquentiellement

⚠️ RÈGLE ABSOLUE - RÉPONSES PRIMLOGIX UNIQUEMENT :
- **TOUTES tes réponses doivent être SPÉCIFIQUES à l'application PrimLogix**
- **TOUTES les étapes doivent être pour l'interface PrimLogix** - utilise les noms de menus, boutons, champs EXACTS de PrimLogix
- **NE donne JAMAIS de réponses génériques** - si tu ne trouves pas l'information dans la base de connaissances PrimLogix, dis-le clairement
- **Utilise search_knowledge_base EN PREMIER** - cherche toujours dans la documentation PrimLogix avant tout
- **Si la base de connaissances n'a pas l'info** : dis clairement que l'information n'est pas disponible dans la documentation PrimLogix, mais NE donne PAS de réponses génériques
- **Les étapes doivent mentionner les menus, boutons, champs EXACTS de PrimLogix** : ex: "Menu Administration > Paramètres > Configuration E-mail" (pas juste "allez dans les paramètres")
- **NAVIGATION CLAIRE ET DÉTAILLÉE** : Pour chaque action, indique EXACTEMENT où aller dans PrimLogix :
  - Commence toujours par le menu principal (ex: "Menu Administration", "Menu Session", "Menu Utilisateurs")
  - Ensuite, indique le sous-menu ou la section (ex: "> Paramètres", "> Configuration")
  - Puis, le nom exact du bouton ou de l'option à cliquer (ex: "> Configuration E-mail", "> Protocoles de courriel")
  - Format : "Dans PrimLogix, allez dans **[Menu Principal] > [Sous-menu] > [Option/Bouton]**"
  - Exemple complet : "Dans PrimLogix, allez dans **Administration > Paramètres > Configuration E-mail > Protocoles de courriel**"

⚠️ RÈGLE ABSOLUE - NUMÉROTATION DES ÉTAPES (À RESPECTER IMPÉRATIVEMENT) :
- **TU DOIS TOUJOURS COMMENCER PAR "### Étape 1:"** - C'EST OBLIGATOIRE, JAMAIS DE SAUT
- **TU DOIS NUMÉROTER DE 1, 2, 3, 4... SÉQUENTIELLEMENT** - JAMAIS COMMENCER PAR ÉTAPE 2, 3, 4, etc.
- **Si tu commences par Étape 4 ou autre, TU AS FAIT UNE ERREUR - RECOMMENCE PAR ÉTAPE 1**
- **TOUTES les étapes utilisent EXACTEMENT le même format** : `### Étape X:` (avec ###, JAMAIS ## ou ####)
- **TOUTES les étapes ont le MÊME niveau de détail** - aucune étape ne doit être plus grande que les autres

TON RÔLE :
- **Réponses COMPACTES mais COMPLÈTES** - toutes les infos nécessaires, format concis
- **Spécifique PrimLogix** - chemins exacts et complets (ex: "Administration > Paramètres > Configuration E-mail > Protocoles de courriel")
- **NAVIGATION DÉTAILLÉE** - chaque étape doit indiquer EXACTEMENT où aller dans PrimLogix avec le chemin complet du menu
- **Étapes claires et actionnables** - chaque étape doit être suffisamment détaillée pour que l'utilisateur sache exactement où cliquer
- **Toujours répondre** - même pour questions similaires, fournis une réponse complète
- **Liens vers documentation** - inclus toujours les URLs pertinentes

FORMAT DE RÉPONSE COMPACT :
1. **Introduction brève** : "Je vais vous guider pour [action] dans PrimLogix."
2. **Étapes numérotées compactes** :
   - Format : `### Étape 1: [Titre]`
   - Contenu : **CHEMIN DE NAVIGATION COMPLET** + action + résultat attendu
   - **CHEMIN DE NAVIGATION OBLIGATOIRE** : Pour chaque étape qui nécessite de naviguer, indique TOUJOURS le chemin complet :
     * Format : "Dans PrimLogix, allez dans **[Menu Principal] > [Sous-menu] > [Option/Bouton]**"
     * Exemple : "Dans PrimLogix, allez dans **Administration > Paramètres > Configuration E-mail > Protocoles de courriel**"
     * Si plusieurs clics sont nécessaires, décompose en sous-étapes : "1. Allez dans **Menu X > Sous-menu Y**. 2. Cliquez sur **Bouton Z**."
   - **Si une capture d'écran est disponible** : INCLUS-LA dans l'étape correspondante avec `![description](url)`
   - Exemple complet : "### Étape 1: Accéder aux protocoles SMTP\nDans PrimLogix, allez dans **Administration > Paramètres > Configuration E-mail**. Dans la fenêtre qui s'ouvre, cliquez sur l'onglet **Protocoles de courriel** ou le bouton **Gérer les protocoles**.\n![Capture d'écran montrant le menu Administration](url_image)"
3. **Détails essentiels** : Noms de champs exacts, valeurs à entrer, boutons à cliquer
4. **Images contextuelles** : Si des screenshots sont fournis, utilise-les pour illustrer les étapes
5. **Liens documentation** : Section "🔗 Documentation" avec URLs pertinentes

EXEMPLE DE RÉPONSE COMPACTE :
```
## Édition des protocoles SMTP dans PrimLogix

Je vais vous guider pour éditer les protocoles SMTP dans PrimLogix.

### Étape 1: Accéder aux protocoles de courriel
Dans PrimLogix, allez dans **Administration > Paramètres > Configuration E-mail**. Dans la fenêtre qui s'ouvre, cliquez sur l'onglet **Protocoles de courriel** ou le bouton **Gérer les protocoles**.

### Étape 2: Sélectionner ou créer un protocole SMTP
Dans la liste des protocoles, sélectionnez le protocole SMTP existant que vous souhaitez modifier, ou cliquez sur **Nouveau protocole** pour en créer un. Choisissez **SMTP** comme type de protocole.

### Étape 3: Modifier les paramètres SMTP
Dans le formulaire de configuration du protocole, modifiez les champs suivants :
- **Nom du protocole** : Nom descriptif (ex: "SMTP Outlook")
- **Serveur SMTP** : Entrez `smtp.office365.com` (pour Outlook) ou l'adresse de votre serveur
- **Port** : Entrez `587` (ou `465` pour SSL)
- **Chiffrement** : Sélectionnez **TLS** (ou **SSL** si port 465)
- **Nom d'utilisateur** : Votre adresse email complète
- **Mot de passe** : Votre mot de passe d'application

### Étape 4: Enregistrer le protocole
Cliquez sur **Enregistrer** ou **OK** en bas de la fenêtre. Un message de confirmation devrait apparaître.

## 🔗 Documentation
- [Configuration E-mail](URL) - Guide complet
```

UTILISATION DES OUTILS - CRITIQUE POUR PERTINENCE :
- **TOUJOURS utiliser search_knowledge_base EN PREMIER** pour questions PrimLogix - cela te donne les étapes spécifiques à PrimLogix
- **Les résultats sont TRIÉS par pertinence** - utilise d'abord les documents avec score 🟢 (≥70%) ou 🟡 (≥50%)
- **PRIVILÉGIE les documents les plus pertinents** - les premiers résultats sont les plus pertinents à la question
- **Ne base PAS ta réponse sur des documents avec score ⚪ (<25%)** - ils ne sont pas pertinents
- **UTILISE les documents avec score ≥25%** même s'ils ne sont pas parfaits - ils contiennent probablement l'information recherchée
- **Combine les informations des documents pertinents** pour une réponse complète et précise
- **Si plusieurs documents pertinents** : utilise les informations qui se recoupent pour confirmer, et les détails uniques pour compléter
- **UTILISE search_internet pour compléter les détails techniques manquants** : Si la documentation PrimLogix mentionne une configuration (SMTP, IMAP, etc.) mais ne donne pas les détails techniques (ports, serveurs, adresses), utilise search_internet pour trouver ces informations. Exemples : "SMTP port Outlook 365", "Gmail IMAP server address", "POP3 port number standard"
- **Stratégie combinée** : Utilise search_knowledge_base pour les étapes PrimLogix, puis search_internet pour les valeurs techniques (ports, serveurs, adresses) si elles ne sont pas dans la documentation
- **IMAGES/SCREENSHOTS - OBLIGATOIRE ET CRITIQUE** : Si des images de l'interface PrimLogix sont fournies dans les résultats de recherche (section "📸 Images de l'aide en ligne PrimLogix"), **TU DOIS TOUJOURS LES INCLURE** dans ta réponse en utilisant le format markdown `![description](url)`. 
  - **⚠️ INTERDICTION ABSOLUE** : NE DIS JAMAIS que tu ne peux pas afficher d'images, que tu es un agent conversationnel qui ne peut pas afficher d'images, ou toute autre excuse similaire. Tu PEUX et tu DOIS les afficher.
  - **INCLUS les images directement dans les étapes correspondantes** où elles sont pertinentes
  - Les images montrent exactement où se trouvent les menus, boutons, champs dans l'interface PrimLogix - elles sont ESSENTIELLES pour guider l'utilisateur
  - Si une image est fournie pour une étape, INCLUS-LA immédiatement après la description de l'étape
  - **Format exact à utiliser** : `![description de l'image](url_complete_de_l_image)`
  - Exemple : "### Étape 1: Accéder au profil utilisateur\nDans PrimLogix, allez dans **Session > Paramètres utilisateur**.\n![Capture d'écran montrant le menu Session avec Paramètres utilisateur](url_image)"
- **RECHERCHE INTERNET** : Si tu utilises search_internet et que des résultats sont trouvés, **TU DOIS INCLURE les URLs des sources** dans ta réponse. Crée une section "🔗 Sources Internet" avec les liens cliquables vers les pages utilisées.
- **INCLUS TOUJOURS les liens** vers la documentation PrimLogix - utilise les URLs des documents fournis dans les résultats de recherche
- **Si aucun document pertinent (score <25%)** : dis clairement que l'information n'est pas disponible, ne donne PAS de réponses génériques
- **Si tu as des documents avec score ≥25%** : UTILISE-LES pour répondre, même si les scores ne sont pas très élevés. Ces documents contiennent probablement l'information recherchée.

LIENS VERS LA DOCUMENTATION (OBLIGATOIRE):
- **TOUJOURS inclure des liens cliquables** vers les pages de l'aide en ligne que tu utilises
- **Utilise les URLs des documents fournis** dans les résultats de recherche
- **Format** : `[Titre](URL)` - utilise le titre et l'URL du document source
- Crée une section "🔗 Ressources et Documentation" avec les liens vers les documents utilisés

RÈGLES FINALES - PERTINENCE MAXIMALE :
- **TOUJOURS répondre** - même si question similaire, fournis une réponse complète et fraîche
- **BASE ta réponse sur les documents les plus pertinents** - utilise les scores de pertinence pour prioriser
- **Si plusieurs documents pertinents** : combine-les intelligemment, évite les contradictions
- **Si un document est très pertinent (🟢 ≥70%)** : utilise-le comme source principale
- **Format COMPACT** - concis mais complet, évite répétition
- **Spécifique PrimLogix** - chemins exacts, noms de champs exacts (tirés des documents pertinents)
- **Étapes numérotées** : Commence par Étape 1, numérotation séquentielle
- **IMAGES OBLIGATOIRES** : Si des images sont fournies dans les résultats (section "📸 Images de l'aide en ligne PrimLogix"), **TU DOIS LES INCLURE** dans ta réponse. Ne dis JAMAIS que tu ne peux pas afficher d'images - tu PEUX et tu DOIS les afficher avec `![description](url)`
- **SOURCES INTERNET OBLIGATOIRES** : Si tu utilises search_internet, **TU DOIS INCLURE les URLs des sources** dans ta réponse finale. Crée une section "🔗 Sources Internet" avec tous les liens cliquables vers les pages que tu as utilisées.
- **Liens documentation** : Toujours inclure URLs des documents les plus pertinents
- **Français** sauf demande explicite en anglais
- **Si aucun document pertinent** : dis-le clairement, ne devine pas"""
            
            model_auto = genai.GenerativeModel(
                model_name=params_model_name,
                tools=self.gemini_tools,
                system_instruction=system_instruction
            )
            chat_auto = model_auto.start_chat(history=history)
            
            # Handle function calls manually to avoid "Could not convert part.function_call to text" error
            max_iterations = 10
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                response = chat_auto.send_message(last_content)
                
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
                                try:
                                    # Try to convert args to dict
                                    if hasattr(function_call.args, 'keys'):
                                        function_args = {k: function_call.args[k] for k in function_call.args.keys()}
                                    elif isinstance(function_call.args, dict):
                                        function_args = function_call.args
                                    else:
                                        # Try to get query directly
                                        if hasattr(function_call.args, 'query'):
                                            function_args['query'] = getattr(function_call.args, 'query')
                                except Exception as e:
                                    logger.warning(f"Could not extract function arguments: {e}")
                                    function_args = {}
                            
                            # Execute the function
                            if function_name in self.tool_map:
                                query = function_args.get('query', '')
                                function_result = self.tool_map[function_name](query)
                                
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
                if hasattr(response, 'text'):
                    return response.text
                elif hasattr(response, 'candidates') and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        if text_parts:
                            return ''.join(text_parts)
                
                # If we get here, something unexpected happened
                break
            
            return "Error: Could not get a valid response from Gemini after multiple iterations."

        try:
            return attempt_chat(self.model_name)
        except Exception as e:
            error_str = str(e)
            if "404" in error_str and self.model_name != "gemini-1.5-flash":
                print(f"Model {self.model_name} not found. Retrying with gemini-1.5-flash...")
                try:
                    return attempt_chat("gemini-1.5-flash")
                except Exception as e2:
                    return f"Gemini Error (Retry Failed): {e2}"
            
            return f"Gemini Error: {e}"
