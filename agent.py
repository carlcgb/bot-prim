try:
    from duckduckgo_search import DDGS
except ImportError:
    from ddgs import DDGS
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
                            description="Search the internet ONLY for general technical issues NOT related to PrimLogix (e.g., general Windows errors, network troubleshooting, general software installation). DO NOT use this for PrimLogix-specific questions - always use search_knowledge_base first for PrimLogix questions.",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "query": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="Technical search query with error codes, technology names, or specific technical problem description."
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


    def _search_kb(self, query):
        print(f"DEBUG: Searching KB for '{query}'")
        try:
            # Search with optimized results for speed and quality
            results = query_knowledge_base(query, n_results=10)
            if not results or not results.get('documents') or not results['documents'][0]:
                # Try alternative search queries if initial search fails
                print(f"DEBUG: Initial search failed, trying alternative queries...")
                alternative_queries = [
                    query.lower(),
                    query.replace("configuration", "config"),
                    query.replace("config", "configuration"),
                    query + " PrimLogix",
                    "PrimLogix " + query
                ]
                
                for alt_query in alternative_queries:
                    if alt_query == query:
                        continue
                    alt_results = query_knowledge_base(alt_query, n_results=6)
                    if alt_results and alt_results.get('documents') and alt_results['documents'][0]:
                        print(f"DEBUG: Found results with alternative query: '{alt_query}'")
                        results = alt_results
                        break
                
                if not results or not results.get('documents') or not results['documents'][0]:
                    return f"No relevant documentation found for '{query}'. Consider trying different search terms or checking if the information exists in the knowledge base."
            
            docs = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results.get('distances', [None])[0] if results.get('distances') else [None] * len(docs)
            
            # Include all results, even lower relevance ones, for comprehensive coverage
            context = f"📚 Technical Documentation Search Results for: '{query}'\n"
            context += f"Found {len(docs)} relevant document(s)\n\n"
            
            seen_docs = set()  # Avoid duplicates
            for i, doc in enumerate(docs):
                if not doc or not doc.strip():
                    continue
                
                # Skip exact duplicates
                doc_hash = hash(doc[:100])  # Use first 100 chars as hash
                if doc_hash in seen_docs:
                    continue
                seen_docs.add(doc_hash)
                
                source = metadatas[i].get('url', 'URL unknown') if i < len(metadatas) else 'URL unknown'
                title = metadatas[i].get('title', 'Untitled') if i < len(metadatas) else 'Untitled'
                chunk_idx = metadatas[i].get('chunk_index', '?') if i < len(metadatas) else '?'
                
                # Calculate relevance score
                relevance_score = ""
                if distances and i < len(distances) and distances[i] is not None:
                    score = max(0, min(100, int((1 - distances[i]) * 100)))
                    if score >= 70:
                        relevance_score = f" [🟢 {score}%]"
                    elif score >= 50:
                        relevance_score = f" [🟡 {score}%]"
                    elif score >= 30:
                        relevance_score = f" [🟠 {score}%]"
                    else:
                        relevance_score = f" [⚪ {score}%]"
                
                # Optimized content length for speed (reduced from 8000 to 5000)
                doc_content = doc[:5000] if len(doc) > 5000 else doc
                if len(doc) > 5000:
                    doc_content += "\n[... truncated ...]"
                
                context += f"### Document #{len(seen_docs)}: {title}{relevance_score}\n"
                context += f"**URL:** {source}\n"
                context += f"**Chunk:** {chunk_idx}\n"
                context += f"**Technical Content:**\n{doc_content}\n"
                context += "---\n\n"
            
            # Add direct links section
            context += "**🔗 Direct Documentation Links:**\n"
            seen_urls = set()
            for i, doc in enumerate(docs):
                if i < len(metadatas):
                    source = metadatas[i].get('url', '')
                    title = metadatas[i].get('title', 'Untitled')
                    if source and source not in seen_urls:
                        seen_urls.add(source)
                        context += f"- [{title}]({source})\n"
            
            return context
        except Exception as e:
            logger.error(f"Error searching KB: {e}", exc_info=True)
            return f"Error searching KB: {e}"

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

⚠️ RÈGLE ABSOLUE - NUMÉROTATION DES ÉTAPES (À RESPECTER IMPÉRATIVEMENT) :
- **TU DOIS TOUJOURS COMMENCER PAR "### Étape 1:"** - C'EST OBLIGATOIRE, JAMAIS DE SAUT
- **TU DOIS NUMÉROTER DE 1, 2, 3, 4... SÉQUENTIELLEMENT** - JAMAIS COMMENCER PAR ÉTAPE 2, 3, 4, etc.
- **Si tu commences par Étape 4 ou autre, TU AS FAIT UNE ERREUR - RECOMMENCE PAR ÉTAPE 1**
- **TOUTES les étapes utilisent EXACTEMENT le même format** : `### Étape X:` (avec ###, JAMAIS ## ou ####)
- **TOUTES les étapes ont le MÊME niveau de détail** - aucune étape ne doit être plus grande que les autres

TON RÔLE :
- **Réponses COMPACTES mais COMPLÈTES** - toutes les infos nécessaires, format concis
- **Spécifique PrimLogix** - chemins exacts (ex: "Administration > Paramètres > Configuration E-mail")
- **Étapes claires** - chaque étape doit être actionnable, format compact
- **Toujours répondre** - même pour questions similaires, fournis une réponse complète
- **Liens vers documentation** - inclus toujours les URLs pertinentes

FORMAT DE RÉPONSE COMPACT :
1. **Introduction brève** : "Je vais vous guider pour [action] dans PrimLogix."
2. **Étapes numérotées compactes** :
   - Format : `### Étape 1: [Titre]`
   - Contenu : Chemin PrimLogix exact + action + résultat attendu (en 1-2 phrases)
   - Exemple : "### Étape 1: Accéder aux paramètres SMTP\nDans PrimLogix, allez dans **Administration > Paramètres > Configuration E-mail**. Cliquez sur **Paramètres SMTP**."
3. **Détails essentiels** : Noms de champs exacts, valeurs à entrer, boutons à cliquer
4. **Liens documentation** : Section "🔗 Documentation" avec URLs pertinentes

EXEMPLE DE RÉPONSE COMPACTE :
```
## Configuration SMTP dans PrimLogix

Je vais vous guider pour configurer votre courriel SMTP avec Outlook dans PrimLogix.

### Étape 1: Accéder aux paramètres SMTP
Dans PrimLogix, allez dans **Administration > Paramètres > Configuration E-mail**. Cliquez sur **Paramètres SMTP**.

### Étape 2: Remplir les champs SMTP
Dans la section **Paramètres SMTP** :
- **Serveur SMTP** : Entrez `smtp.office365.com`
- **Port** : Entrez `587`
- **Chiffrement** : Sélectionnez **TLS**
- **Nom d'utilisateur** : Votre adresse email Outlook
- **Mot de passe** : Votre mot de passe d'application (pas votre mot de passe normal)

### Étape 3: Enregistrer
Cliquez sur **Enregistrer** en bas de la fenêtre. Un message de confirmation devrait apparaître.

## 🔗 Documentation
- [Configuration E-mail](URL) - Guide complet
```

UTILISATION DES OUTILS :
- **TOUJOURS utiliser search_knowledge_base EN PREMIER** pour questions PrimLogix
- **Une recherche suffit généralement** - seulement si vraiment nécessaire, essaie une variante
- **Analyse les résultats** et combine les infos pour une réponse complète
- **INCLUS TOUJOURS les liens** vers la documentation PrimLogix
- Si info non trouvée : dis-le clairement, ne donne PAS de réponses génériques

LIENS VERS LA DOCUMENTATION (OBLIGATOIRE):
- **TOUJOURS inclure des liens cliquables** vers les pages/sections pertinentes de l'aide en ligne
- Utilise le format markdown : `[Titre de la section](URL)`
- Inclus les URLs complètes des documents sources dans chaque réponse
- Crée une section "🔗 Ressources et Documentation" avec tous les liens pertinents
- Les liens doivent mener directement à l'endroit pertinent dans l'aide en ligne

RÈGLES FINALES :
- **TOUJOURS répondre** - même si question similaire, fournis une réponse complète et fraîche
- **Format COMPACT** - concis mais complet, évite répétition
- **Spécifique PrimLogix** - chemins exacts, noms de champs exacts
- **Étapes numérotées** : Commence par Étape 1, numérotation séquentielle
- **Liens documentation** : Toujours inclure URLs pertinentes
- **Français** sauf demande explicite en anglais"""
            
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
