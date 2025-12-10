from openai import OpenAI
try:
    from duckduckgo_search import DDGS
except ImportError:
    from ddgs import DDGS
from knowledge_base import query_knowledge_base
import json
import logging
import google.generativeai as genai
from google.generativeai.types import content_types
from collections import defaultdict

logger = logging.getLogger(__name__)

class PrimAgent:
    def __init__(self, api_key, base_url=None, model="gpt-3.5-turbo", provider="OpenAI"):
        self.provider = provider
        self.model_name = model
        self.ddgs = DDGS()
        
        # Tools definition for OpenAI
        self.openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge_base",
                    "description": "Search the PrimLogix technical documentation for debugging client issues. Use this for: PrimLogix-specific errors, field configurations, database issues, API problems, feature implementation details, configuration parameters, and technical procedures. IMPORTANT: If the first search doesn't return enough results, try multiple searches with different query terms (synonyms, related terms, broader/narrower terms) to find all relevant information.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Technical search query. Include: error codes, field names, feature names, configuration paths, database references, or specific technical terms from PrimLogix. Try multiple variations if first search doesn't find enough information."
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_internet",
                    "description": "Search the internet for general technical debugging information. Use this for: email/SMTP configuration issues, network problems, database connection errors, API authentication issues, general software errors, or technical solutions not specific to PrimLogix.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Technical search query with error codes, technology names, or specific technical problem description."
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

        if self.provider == "Google Gemini":
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
                            description="Search the internet for general technical debugging information. Use this for: email/SMTP configuration issues, network problems, database connection errors, API authentication issues, general software errors, or technical solutions not specific to PrimLogix.",
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

        else:
            self.client = OpenAI(api_key=api_key, base_url=base_url)


    def _search_kb(self, query):
        print(f"DEBUG: Searching KB for '{query}'")
        try:
            # Search with more results for comprehensive coverage
            results = query_knowledge_base(query, n_results=15)
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
                    alt_results = query_knowledge_base(alt_query, n_results=10)
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
                
                # Keep more content for better context (increased from 6000 to 8000)
                doc_content = doc[:8000] if len(doc) > 8000 else doc
                if len(doc) > 8000:
                    doc_content += "\n[... truncated for context ...]"
                
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
        if self.provider == "Google Gemini":
            return self._run_gemini(messages)
        else:
            return self._run_openai(messages)

    def _run_openai(self, messages):
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
            # Technical system instruction for debugging-oriented responses
            system_instruction = """Tu es PRIMBOT, un assistant technique de débogage pour le logiciel PrimLogix. Ton rôle est d'aider les développeurs et le support technique à déboguer efficacement les problèmes des clients.

ORIENTATION TECHNIQUE:
- Fournis des informations techniques, concises et actionnables pour le débogage
- Concentre-toi sur les causes racines, codes d'erreur, problèmes de configuration et solutions techniques
- Utilise la terminologie technique (noms de champs, codes d'erreur, endpoints API, requêtes base de données)
- Inclus des détails techniques spécifiques : IDs de champs, noms de tables, chemins de configuration, patterns de logs
- Priorise les étapes de diagnostic et procédures de dépannage

STRUCTURE DE RÉPONSE:
1. **Diagnostic Rapide** : Évaluation technique immédiate du problème
2. **Analyse de Cause Racine** : Explication technique de pourquoi le problème se produit
3. **Solution Technique** : Correction étape par étape avec détails spécifiques
4. **Étapes de Vérification** : Vérifications techniques pour confirmer la résolution
5. **Problèmes Connexes** : Problèmes techniques courants liés et leurs solutions

DÉTAILS TECHNIQUES À INCLURE:
- Noms de champs exacts, IDs et références base de données
- Codes d'erreur et leurs significations
- Chemins de fichiers de configuration et noms de paramètres
- Endpoints API et formats de requête/réponse
- Noms de tables/colonnes base de données quand pertinent
- Emplacements de fichiers de logs et ce qu'il faut chercher
- Étapes de dépannage réseau/connexion

UTILISATION DES OUTILS:
- TOUJOURS rechercher dans la base de connaissances EN PREMIER pour les questions PrimLogix - essaie plusieurs requêtes de recherche avec des termes différents si la première recherche ne trouve pas assez d'informations
- Si la recherche dans la base de connaissances retourne peu ou pas de résultats, essaie des termes de recherche alternatifs (synonymes, termes liés, termes plus larges/plus étroits)
- Utilise search_internet pour les problèmes techniques généraux (config email, SMTP, problèmes réseau, etc.) OU quand la base de connaissances n'a pas l'information
- Si la recherche initiale trouve peu d'informations, effectue des recherches supplémentaires avec des termes liés pour obtenir une couverture complète
- Combine plusieurs résultats de recherche de la base de connaissances et d'internet pour des réponses techniques complètes
- N'abandonne pas après une recherche - sois minutieux et recherche plusieurs fois avec des variations de requête différentes

STYLE DE RÉPONSE:
- Sois direct et technique - pas d'explications inutiles
- Utilise des blocs de code pour exemples de configuration, requêtes SQL ou instructions ligne de commande
- Inclus des valeurs spécifiques, chemins et références techniques
- Fournis plusieurs approches de solution quand applicable
- Référence les URLs de documentation pour informations techniques détaillées

LANGUE:
- Réponds en français sauf si l'utilisateur demande en anglais
- Utilise la terminologie technique française de la documentation PrimLogix"""
            
            model_auto = genai.GenerativeModel(
                model_name=params_model_name,
                tools=self.gemini_tools,
                system_instruction=system_instruction
            )
            chat_auto = model_auto.start_chat(history=history, enable_automatic_function_calling=True)
            return chat_auto.send_message(last_content).text

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
